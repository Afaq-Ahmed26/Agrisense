from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SensorReadingBase(BaseModel):
    device_id: str
    soil_moisture: float
    temperature: float
    humidity: float
    light_level: float


class SensorReadingCreate(SensorReadingBase):
    timestamp: Optional[datetime] = None


class SensorReading(SensorReadingBase):
    id: str
    timestamp: datetime

    class Config:
        from_attributes = True


class DeviceBase(BaseModel):
    name: str
    location: str
    owner_id: str
    type: str = "irrigation_device"


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