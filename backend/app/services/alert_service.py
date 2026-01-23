from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel
from app.services.firebase_service import firebase_service


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
        self.alert_thresholds = {
            "soil_moisture_low": 30,  # percentage
            "soil_moisture_critical": 20,  # percentage
            "temperature_high": 40,  # Celsius
            "temperature_critical": 45,  # Celsius
            "humidity_low": 20,  # percentage
            "humidity_high": 85,  # percentage
        }
    
    def evaluate_sensor_data(self, sensor_data: Dict) -> List[Alert]:
        """
        Evaluate sensor data against thresholds and generate alerts if needed.
        """
        alerts = []
        device_id = sensor_data.get("device_id")
        timestamp = sensor_data.get("timestamp", datetime.utcnow())
        
        # Check soil moisture levels
        soil_moisture = sensor_data.get("soil_moisture")
        if soil_moisture is not None:
            if soil_moisture < self.alert_thresholds["soil_moisture_critical"]:
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
            elif soil_moisture < self.alert_thresholds["soil_moisture_low"]:
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
            if temperature > self.alert_thresholds["temperature_critical"]:
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
            elif temperature > self.alert_thresholds["temperature_high"]:
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
            if humidity < self.alert_thresholds["humidity_low"]:
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
            elif humidity > self.alert_thresholds["humidity_high"]:
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
        Save an alert to the database.
        """
        # In a real implementation, we would save this to Firestore
        # firebase_service.db.collection('alerts').document(alert.id).set(alert.dict())
        print(f"Created alert: {alert.message}")
    
    async def get_device_alerts(self, device_id: str, status: Optional[AlertStatus] = None) -> List[Alert]:
        """
        Retrieve alerts for a specific device.
        """
        # In a real implementation, we would fetch from Firestore
        # with appropriate filters
        return []
    
    async def get_open_alerts(self) -> List[Alert]:
        """
        Retrieve all open alerts across all devices.
        """
        # In a real implementation, we would fetch from Firestore
        # with status = "open" filter
        return []
    
    async def acknowledge_alert(self, alert_id: str, user_id: str):
        """
        Acknowledge an alert.
        """
        # In a real implementation, we would update the alert in Firestore
        pass
    
    async def resolve_alert(self, alert_id: str, user_id: str):
        """
        Resolve an alert.
        """
        # In a real implementation, we would update the alert in Firestore
        pass


# Global instance
alert_service = AlertService()