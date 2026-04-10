import asyncio
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
        # NEW: Cache for current active alert statuses to prevent duplicate alerts
        # Stores the last known severity for a (device_id, alert_type) pair
        self._active_alert_statuses: Dict[str, Dict[AlertType, AlertSeverity]] = {} 

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
    
    async def evaluate_sensor_data(self, sensor_data: Dict) -> List[Alert]:
        """
        Evaluate sensor data against thresholds and generate alerts if needed.
        Only creates new alerts if the state has changed, using RAM cache to minimize Firestore reads.
        """
        device_id = sensor_data.get("device_id")
        timestamp = sensor_data.get("timestamp", datetime.utcnow())
        thresholds = await asyncio.to_thread(self._get_thresholds)
        
        generated_alerts = []
        
        # Initialize device's alert status in cache if not present
        if device_id not in self._active_alert_statuses:
            self._active_alert_statuses[device_id] = {}

        # --- Evaluate Soil Moisture ---
        soil_moisture = sensor_data.get("soil_moisture")
        current_moisture_severity = None
        if soil_moisture is not None:
            if soil_moisture < thresholds.soil_moisture_critical:
                current_moisture_severity = AlertSeverity.CRITICAL
            elif soil_moisture < thresholds.soil_moisture_low:
                current_moisture_severity = AlertSeverity.HIGH
        
        previous_moisture_severity = self._active_alert_statuses[device_id].get(AlertType.SOIL_MOISTURE_LOW)

        if current_moisture_severity != previous_moisture_severity:
            # State has changed, create/resolve alert
            if current_moisture_severity:
                # RAM CACHE CHECK: Only create if the severity has actually changed
                # This avoids the expensive Firestore query on every 2s POST
                alert = Alert(
                    id=f"alert_{timestamp.timestamp()}_{device_id}_moisture_{current_moisture_severity.value}",
                    device_id=device_id,
                    alert_type=AlertType.SOIL_MOISTURE_LOW,
                    severity=current_moisture_severity,
                    message=f"Soil moisture {current_moisture_severity.value.lower()}: {soil_moisture}%",
                    timestamp=timestamp
                )
                generated_alerts.append(alert)
                self._active_alert_statuses[device_id][AlertType.SOIL_MOISTURE_LOW] = current_moisture_severity
            else:
                # Condition cleared (returned to normal)
                if previous_moisture_severity:
                    await self._resolve_latest_alert_by_type(device_id, AlertType.SOIL_MOISTURE_LOW)
                    self._active_alert_statuses[device_id].pop(AlertType.SOIL_MOISTURE_LOW, None)

        # --- Evaluate Temperature ---
        temperature = sensor_data.get("temperature")
        current_temp_severity = None
        if temperature is not None:
            if temperature > thresholds.temperature_critical:
                current_temp_severity = AlertSeverity.CRITICAL
            elif temperature > thresholds.temperature_high:
                current_temp_severity = AlertSeverity.MEDIUM
        
        previous_temp_severity = self._active_alert_statuses[device_id].get(AlertType.DEVICE_ERROR)

        if current_temp_severity != previous_temp_severity:
            if current_temp_severity:
                alert = Alert(
                    id=f"alert_{timestamp.timestamp()}_{device_id}_temp_{current_temp_severity.value}",
                    device_id=device_id,
                    alert_type=AlertType.DEVICE_ERROR,
                    severity=current_temp_severity,
                    message=f"Temperature {current_temp_severity.value.lower()}: {temperature}°C",
                    timestamp=timestamp
                )
                generated_alerts.append(alert)
                self._active_alert_statuses[device_id][AlertType.DEVICE_ERROR] = current_temp_severity
            else:
                if previous_temp_severity:
                    await self._resolve_latest_alert_by_type(device_id, AlertType.DEVICE_ERROR)
                    self._active_alert_statuses[device_id].pop(AlertType.DEVICE_ERROR, None)

        # --- Evaluate Humidity ---
        humidity = sensor_data.get("humidity")
        current_humidity_severity = None
        if humidity is not None:
            if humidity < thresholds.humidity_low:
                current_humidity_severity = AlertSeverity.MEDIUM
            elif humidity > thresholds.humidity_high:
                current_humidity_severity = AlertSeverity.MEDIUM
        
        previous_humidity_severity = self._active_alert_statuses[device_id].get(AlertType.UNUSUAL_READING)

        if current_humidity_severity != previous_humidity_severity:
            if current_humidity_severity:
                alert = Alert(
                    id=f"alert_{timestamp.timestamp()}_{device_id}_humidity_{current_humidity_severity.value}",
                    device_id=device_id,
                    alert_type=AlertType.UNUSUAL_READING,
                    severity=current_humidity_severity,
                    message=f"Humidity {current_humidity_severity.value.lower()}: {humidity}%",
                    timestamp=timestamp
                )
                generated_alerts.append(alert)
                self._active_alert_statuses[device_id][AlertType.UNUSUAL_READING] = current_humidity_severity
            else:
                if previous_humidity_severity:
                    await self._resolve_latest_alert_by_type(device_id, AlertType.UNUSUAL_READING)
                    self._active_alert_statuses[device_id].pop(AlertType.UNUSUAL_READING, None)
        
        return generated_alerts
        
        return generated_alerts
    
    async def _resolve_latest_alert_by_type(self, device_id: str, alert_type: AlertType):
        """
        Resolves the latest open alert of a specific type for a device in Firestore.
        """
        query = (
            firebase_service.db.collection('alerts')
            .where(filter=FieldFilter("device_id", "==", device_id))
            .where(filter=FieldFilter("alert_type", "==", alert_type.value))
            .where(filter=FieldFilter("status", "==", AlertStatus.OPEN.value))
            .order_by("timestamp", direction="DESCENDING")
            .limit(1)
        )
        # Use to_thread for the blocking query stream
        docs = await asyncio.to_thread(lambda: [doc for doc in query.stream()])
        if docs:
            latest_alert_doc = docs[0]
            alert_ref = firebase_service.db.collection('alerts').document(latest_alert_doc.id)
            await asyncio.to_thread(alert_ref.update, {"status": AlertStatus.RESOLVED.value, "resolved_at": datetime.utcnow()})
            print(f"Resolved alert {latest_alert_doc.id} for device {device_id}, type {alert_type.value}")
    
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
        alert_ref = firebase_service.db.collection('alerts').document(alert.id)
        await asyncio.to_thread(alert_ref.set, alert.model_dump())
        print(f"Saved alert to Firestore: {alert.message}")

        # Fetch device owner (using cache if available)
        owner_id = self._device_owner_cache.get(alert.device_id)
        if not owner_id:
            device_ref = firebase_service.db.collection('devices').document(alert.device_id)
            device_doc = await asyncio.to_thread(device_ref.get)
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
                prefs_doc = await asyncio.to_thread(prefs_ref.get)
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
                await notification_service.create_notification(notification_data, owner_id)
                print(f"Created in-app notification for user {owner_id}")
            elif channel == 'email':
                user_doc = await asyncio.to_thread(firebase_service.db.collection('users').document(owner_id).get)
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
        
        docs = await asyncio.to_thread(lambda: [doc for doc in query.stream()])
        alerts = [Alert(**doc.to_dict()) for doc in docs]
        return alerts
    
    async def get_open_alerts(self) -> List[Alert]:
        """
        Retrieve all open alerts across all devices.
        """
        query = firebase_service.db.collection('alerts').where(filter=FieldFilter("status", "==", AlertStatus.OPEN.value))
        docs = await asyncio.to_thread(lambda: [doc for doc in query.stream()])
        alerts = [Alert(**doc.to_dict()) for doc in docs]
        return alerts
    
    async def acknowledge_alert(self, alert_id: str, user_id: str):
        """
        Acknowledge an alert.
        """
        alert_ref = firebase_service.db.collection('alerts').document(alert_id)
        await asyncio.to_thread(alert_ref.update, {
            "status": AlertStatus.ACKNOWLEDGED.value,
            "acknowledged_by": user_id,
            "acknowledged_at": datetime.utcnow()
        })
    
    async def resolve_alert(self, alert_id: str, user_id: str):
        """
        Resolve an alert.
        """
        alert_ref = firebase_service.db.collection('alerts').document(alert_id)
        await asyncio.to_thread(alert_ref.update, {
            "status": AlertStatus.RESOLVED.value,
            "resolved_by": user_id,
            "resolved_at": datetime.utcnow()
        })


# Global instance
alert_service = AlertService()
