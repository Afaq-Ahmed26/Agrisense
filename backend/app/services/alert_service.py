import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel
from app.models.notification import NotificationCreate
from app.services import notification_service
from app.models.thresholds import AlertThresholds
from app.models.notification_preferences import NotificationPreferences
from app.repositories.alert_repository import alert_repository
from app.repositories.threshold_repository import threshold_repository
from app.repositories.device_repository import device_repository
from app.repositories.user_repository import user_repository


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
        # RAM caches to minimize DB reads
        self._device_owner_cache = {} # device_id -> owner_id
        self._user_prefs_cache = {}   # owner_id -> NotificationPreferences
        self._cache_clear_time = datetime.utcnow()
        self._active_alert_statuses: Dict[str, Dict[AlertType, AlertSeverity]] = {} 

    async def _get_thresholds(self) -> AlertThresholds:
        """
        Retrieves alert thresholds from PostgreSQL, with in-memory caching.
        """
        now = datetime.utcnow()
        if (self._thresholds_cache and self._last_cache_time and
                (now - self._last_cache_time) < self._cache_expiry):
            return self._thresholds_cache

        pg_thresholds = await asyncio.to_thread(threshold_repository.get_alert_thresholds)
        self._thresholds_cache = pg_thresholds or AlertThresholds()
        
        self._last_cache_time = now
        return self._thresholds_cache
    
    async def evaluate_sensor_data(self, sensor_data: Dict) -> List[Alert]:
        """
        Evaluate sensor data against thresholds and generate alerts if needed.
        """
        device_id = sensor_data.get("device_id")
        timestamp = sensor_data.get("timestamp", datetime.utcnow())
        thresholds = await self._get_thresholds()
        
        generated_alerts = []
        
        if device_id not in self._active_alert_statuses:
            self._active_alert_statuses[device_id] = {}

        # Evaluate Soil Moisture
        soil_moisture = sensor_data.get("soil_moisture")
        current_moisture_severity = None
        if soil_moisture is not None:
            if soil_moisture < thresholds.soil_moisture_critical:
                current_moisture_severity = AlertSeverity.CRITICAL
            elif soil_moisture < thresholds.soil_moisture_low:
                current_moisture_severity = AlertSeverity.HIGH
        
        previous_moisture_severity = self._active_alert_statuses[device_id].get(AlertType.SOIL_MOISTURE_LOW)

        if current_moisture_severity != previous_moisture_severity:
            if current_moisture_severity:
                alert = Alert(
                    id=f"active_alert_{device_id}_{AlertType.SOIL_MOISTURE_LOW.value}",
                    device_id=device_id,
                    alert_type=AlertType.SOIL_MOISTURE_LOW,
                    severity=current_moisture_severity,
                    message=f"Soil moisture {current_moisture_severity.value.lower()}: {soil_moisture}%",
                    timestamp=timestamp
                )
                generated_alerts.append(alert)
                self._active_alert_statuses[device_id][AlertType.SOIL_MOISTURE_LOW] = current_moisture_severity
            else:
                if previous_moisture_severity:
                    await self._resolve_latest_alert_by_type(device_id, AlertType.SOIL_MOISTURE_LOW)
                    self._active_alert_statuses[device_id].pop(AlertType.SOIL_MOISTURE_LOW, None)

        # Evaluate Temperature
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
                    id=f"active_alert_{device_id}_{AlertType.DEVICE_ERROR.value}",
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

        return generated_alerts
    
    async def _resolve_latest_alert_by_type(self, device_id: str, alert_type: AlertType):
        """
        Resolves the latest open alert of a specific type for a device in PostgreSQL.
        """
        await asyncio.to_thread(alert_repository.resolve_latest_open_by_type, device_id, alert_type.value)
    
    async def create_alert(self, alert: Alert):
        """
        Save an alert to PostgreSQL and create a notification based on user preferences.
        """
        now = datetime.utcnow()
        if (now - self._cache_clear_time) > timedelta(hours=1):
            self._device_owner_cache.clear()
            self._user_prefs_cache.clear()
            self._cache_clear_time = now

        payload = alert.model_dump()
        payload["alert_type"] = alert.alert_type.value
        payload["severity"] = alert.severity.value
        payload["status"] = alert.status.value
        await asyncio.to_thread(alert_repository.upsert, payload)
        print(f"Saved alert to PostgreSQL: {alert.message}")

        # Fetch device owner
        owner_id = self._device_owner_cache.get(alert.device_id)
        if not owner_id:
            device_data = await asyncio.to_thread(device_repository.get_raw_by_id, alert.device_id)
            owner_id = (device_data or {}).get("owner_id")
            if owner_id:
                self._device_owner_cache[alert.device_id] = owner_id

        if owner_id:
            # Fetch user's notification preferences from PostgreSQL
            prefs = self._user_prefs_cache.get(owner_id)
            if not prefs:
                user = await asyncio.to_thread(user_repository.get_by_id, owner_id, True)
                if user and user.notification_preferences:
                    prefs = NotificationPreferences(**user.notification_preferences)
                else:
                    prefs = NotificationPreferences()
                self._user_prefs_cache[owner_id] = prefs

            # Determine channel
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
            elif channel == 'email':
                user = await asyncio.to_thread(user_repository.get_by_id, owner_id, True)
                if user and user.email:
                    print(f"INFO: Would send email alert to {user.email}: {alert.message}")
    
    async def get_device_alerts(self, device_id: str, status: Optional[AlertStatus] = None) -> List[Alert]:
        rows = await asyncio.to_thread(
            alert_repository.get_by_device,
            device_id,
            status.value if status else None,
            50,
        )
        return [Alert(**row) for row in rows]
    
    async def get_open_alerts(self) -> List[Alert]:
        rows = await asyncio.to_thread(alert_repository.get_open, 50)
        return [Alert(**row) for row in rows]
    
    async def acknowledge_alert(self, alert_id: str, user_id: str):
        await asyncio.to_thread(alert_repository.acknowledge, alert_id, user_id)
    
    async def resolve_alert(self, alert_id: str, user_id: str):
        await asyncio.to_thread(alert_repository.resolve, alert_id, user_id)


# Global instance
alert_service = AlertService()
