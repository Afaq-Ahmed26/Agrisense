from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class IrrigationScheduleBase(BaseModel):
    device_id: str
    start_time: datetime
    duration_minutes: int
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None  # daily, weekly, monthly


class IrrigationScheduleCreate(IrrigationScheduleBase):
    pass


class IrrigationScheduleUpdate(BaseModel):
    start_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    is_active: Optional[bool] = None


class IrrigationSchedule(IrrigationScheduleBase):
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True


class IrrigationEventBase(BaseModel):
    device_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_actual_minutes: Optional[int] = None
    status: str = "pending"  # pending, active, completed, failed


class IrrigationEventCreate(IrrigationEventBase):
    pass


class IrrigationEvent(IrrigationEventBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True