from pydantic import BaseModel

class AlertThresholds(BaseModel):
    soil_moisture_low: float = 30.0
    soil_moisture_critical: float = 20.0
    temperature_high: float = 40.0
    temperature_critical: float = 45.0
    humidity_low: float = 20.0
    humidity_high: float = 85.0
