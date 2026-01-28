from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict


class ActivityLog(BaseModel):
    id: str
    timestamp: datetime
    user_id: str
    action: str
    details: Optional[Dict] = None

    class Config:
        from_attributes = True
