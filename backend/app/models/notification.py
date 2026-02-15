from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationBase(BaseModel):
    user_id: str
    message: str
    type: str  # e.g., 'alert', 'info', 'warning'

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_archived: Optional[bool] = None

class Notification(NotificationBase):
    id: str
    created_at: datetime
    is_read: bool = False
    is_archived: bool = False

    class Config:
        from_attributes = True
