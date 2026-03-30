from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel
from google.cloud.firestore_v1.base_query import FieldFilter
from app.services.firebase_service import firebase_service
from app.models.notification import NotificationCreate
from app.services import notification_service
from app.models.thresholds import AlertThresholds
from app.models.notification_preferences import NotificationPreferences


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertType(str, Enum):
    SOIL_MOISTURE_LOW = "soil_moisture_low"
    SENSOR_OFFLINE = "sensor_offline"
    DEVICE_ERROR = "device_error"
    IRRIGATION_FAILED = "irrigation_failed"
    UNUSUAL_READING = "unusual_reading"


class Alert(BaseModel):
    id: str
    device_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    timestamp: datetime
    status: AlertStatus = AlertStatus.OPEN
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None


class AlertService:
    """
    Service to handle alert generation, storage, and management.
    """
    
    def __init__(self):
        self._thresholds_cache: Optional[AlertThresholds] = None
        self._cache_expiry = timedelta(hours=1)
        self._last_cache_time: Optional[datetime] = None
        # NEW: Cache for device metadata to save reads
        self._device_owner_cache = {} # device_id -> owner_id
        self._user_prefs_cache = {}   # owner_id -> NotificationPreferences
        self._cache_clear_time = datetime.utcnow()

    def _get_thresholds(self) -> AlertThresholds:
        """
        Retrieves alert thresholds from Firestore, with in-memory caching.
        """
        now = datetime.utcnow()
        if (self._thresholds_cache and self._last_cache_time and
                (now - self._last_cache_time) < self._cache_expiry):
            return self._thresholds_cache

        settings_ref = firebase_service.db.collection('system_settings').document('alert_thresholds')
        doc = settings_ref.get()
        if doc.exists:
            self._thresholds_cache = AlertThresholds(**doc.to_dict())
        else:
            # Use default values if not set in DB
            self._thresholds_cache = AlertThresholds()
        
        self._last_cache_time = now
        return self._thresholds_cache
    
    def evaluate_sensor_data(self, sensor_data: Dict) -> List[Alert]:
        """
        Evaluate sensor data against thresholds and generate alerts if needed.
        """
        alerts = []
        device_id = sensor_data.get("device_id")
        timestamp = sensor_data.get("timestamp", datetime.utcnow())
        thresholds = self._get_thresholds()
        
        # Check soil moisture levels
        soil_moisture = sensor_data.get("soil_moisture")
        if soil_moisture is not None:
            if soil_moisture < thresholds.soil_moisture_critical:
                alerts.append(
                    Alert(
                        id=f"alert_{timestamp.timestamp()}_{device_id}_moisture_critical",
                        device_id=device_id,
                        alert_type=AlertType.SOIL_MOISTURE_LOW,
                        severity=AlertSeverity.CRITICAL,
                        message=f"Soil moisture critically low: {soil_moisture}%",
                        timestamp=timestamp
                    )
                )
            elif soil_moisture < thresholds.soil_moisture_low:
                alerts.append(
                    Alert(
                        id=f"alert_{timestamp.timestamp()}_{device_id}_moisture_low",
                        device_id=device_id,
                        alert_type=AlertType.SOIL_MOISTURE_LOW,
                        severity=AlertSeverity.HIGH,
                        message=f"Soil moisture low: {soil_moisture}%",
                        timestamp=timestamp
                    )
                )
        
        # Check temperature levels
        temperature = sensor_data.get("temperature")
        if temperature is not None:
            if temperature > thresholds.temperature_critical:
                alerts.append(
                    Alert(
                        id=f"alert_{timestamp.timestamp()}_{device_id}_temp_critical",
                        device_id=device_id,
                        alert_type=AlertType.DEVICE_ERROR,
                        severity=AlertSeverity.CRITICAL,
                        message=f"Temperature critically high: {temperature}°C",
                        timestamp=timestamp
                    )
                )
            elif temperature > thresholds.temperature_high:
                alerts.append(
                    Alert(
                        id=f"alert_{timestamp.timestamp()}_{device_id}_temp_high",
                        device_id=device_id,
                        alert_type=AlertType.DEVICE_ERROR,
                        severity=AlertSeverity.MEDIUM,
                        message=f"Temperature high: {temperature}°C",
                        timestamp=timestamp
                    )
                )
        
        # Check humidity levels
        humidity = sensor_data.get("humidity")
        if humidity is not None:
            if humidity < thresholds.humidity_low:
                alerts.append(
                    Alert(
                        id=f"alert_{timestamp.timestamp()}_{device_id}_humidity_low",
                        device_id=device_id,
                        alert_type=AlertType.UNUSUAL_READING,
                        severity=AlertSeverity.MEDIUM,
                        message=f"Humidity unusually low: {humidity}%",
                        timestamp=timestamp
                    )
                )
            elif humidity > thresholds.humidity_high:
                alerts.append(
                    Alert(
                        id=f"alert_{timestamp.timestamp()}_{device_id}_humidity_high",
                        device_id=device_id,
                        alert_type=AlertType.UNUSUAL_READING,
                        severity=AlertSeverity.MEDIUM,
                        message=f"Humidity unusually high: {humidity}%",
                        timestamp=timestamp
                    )
                )
        
        return alerts
    
    async def create_alert(self, alert: Alert):
        """
        Save an alert to the database and create a notification based on user preferences.
        """
        now = datetime.utcnow()
        # Periodic cache clear (every hour)
        if (now - self._cache_clear_time) > timedelta(hours=1):
            self._device_owner_cache.clear()
            self._user_prefs_cache.clear()
            self._cache_clear_time = now

        # Save alert to Firestore
        firebase_service.db.collection('alerts').document(alert.id).set(alert.model_dump())
        print(f"Saved alert to Firestore: {alert.message}")

        # Fetch device owner (using cache if available)
        owner_id = self._device_owner_cache.get(alert.device_id)
        if not owner_id:
            device_ref = firebase_service.db.collection('devices').document(alert.device_id)
            device_doc = device_ref.get()
            if device_doc.exists:
                device_data = device_doc.to_dict()
                owner_id = device_data.get("owner_id")
                if owner_id:
                    self._device_owner_cache[alert.device_id] = owner_id

        if owner_id:
            # Fetch user's notification preferences (using cache if available)
            prefs = self._user_prefs_cache.get(owner_id)
            if not prefs:
                prefs_ref = firebase_service.db.collection('notification_preferences').document(owner_id)
                prefs_doc = prefs_ref.get()
                prefs = NotificationPreferences(**prefs_doc.to_dict()) if prefs_doc.exists else NotificationPreferences()
                self._user_prefs_cache[owner_id] = prefs

            # Determine which channel to use based on severity
            channel_map = {
                AlertSeverity.CRITICAL: prefs.on_critical_alert,
                AlertSeverity.HIGH: prefs.on_high_alert,
                AlertSeverity.MEDIUM: prefs.on_medium_alert,
                AlertSeverity.LOW: prefs.on_low_alert,
            }
            channel = channel_map.get(alert.severity)

            if channel == 'in_app':
                notification_data = NotificationCreate(
                    user_id=owner_id,
                    message=alert.message,
                    type=alert.severity.value
                )
                notification_service.create_notification(notification_data, owner_id)
                print(f"Created in-app notification for user {owner_id}")
            elif channel == 'email':
                user_doc = firebase_service.db.collection('users').document(owner_id).get()
                if user_doc.exists:
                    user_email = user_doc.to_dict().get('email')
                    if user_email:
                        print(f"INFO: Would send email alert to {user_email}: {alert.message}")
            elif channel == 'none':
                print(f"INFO: Notification for user {owner_id} suppressed by user preference.")
    
    async def get_device_alerts(self, device_id: str, status: Optional[AlertStatus] = None) -> List[Alert]:
        """
        Retrieve alerts for a specific device.
        """
        query = firebase_service.db.collection('alerts').where(filter=FieldFilter("device_id", "==", device_id))
        if status:
            query = query.where(filter=FieldFilter("status", "==", status.value))
        
        alerts = [Alert(**doc.to_dict()) for doc in query.stream()]
        return alerts
    
    async def get_open_alerts(self) -> List[Alert]:
        """
        Retrieve all open alerts across all devices.
        """
        query = firebase_service.db.collection('alerts').where(filter=FieldFilter("status", "==", AlertStatus.OPEN.value))
        alerts = [Alert(**doc.to_dict()) for doc in query.stream()]
        return alerts
    
    async def acknowledge_alert(self, alert_id: str, user_id: str):
        """
        Acknowledge an alert.
        """
        alert_ref = firebase_service.db.collection('alerts').document(alert_id)
        alert_ref.update({
            "status": AlertStatus.ACKNOWLEDGED.value,
            "acknowledged_by": user_id,
            "acknowledged_at": datetime.utcnow()
        })
    
    async def resolve_alert(self, alert_id: str, user_id: str):
        """
        Resolve an alert.
        """
        alert_ref = firebase_service.db.collection('alerts').document(alert_id)
        alert_ref.update({
            "status": AlertStatus.RESOLVED.value,
            "resolved_by": user_id,
            "resolved_at": datetime.utcnow()
        })



# Global instance
alert_service = AlertService()
