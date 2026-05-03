from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SensorReadingBase(BaseModel):
    device_id: str
    soil_moisture: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    light_level: Optional[float] = None


class SensorReadingCreate(SensorReadingBase):
    timestamp: Optional[datetime] = None


class SensorReading(SensorReadingBase):
    id: str
    timestamp: datetime

    class Config:
        from_attributes = True


class DeviceBase(BaseModel):
    name: str
    location: Optional[str] = None
    owner_id: str
    type: str = "irrigation_device"
    zone_id: Optional[str] = None # Added for grouping
    crop_type: Optional[str] = None # Added for ML context
    area_size: Optional[float] = None # Added for ML context


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None


class Device(DeviceBase):
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True


class HourlyAverageReadings(BaseModel):
    device_id: str
    soil_moisture_avg: float
    temperature_avg: float
    humidity_avg: float
    light_level_avg: float
    count: int

class SensorSummaryValue(BaseModel):
    min: float
    max: float
    avg: float

class DailySummaryReadings(BaseModel):
    device_id: str
    date: str # ISO formatted date string
    count: int
    soil_moisture: SensorSummaryValue
    temperature: SensorSummaryValue
    humidity: SensorSummaryValue
    light_level: SensorSummaryValue
