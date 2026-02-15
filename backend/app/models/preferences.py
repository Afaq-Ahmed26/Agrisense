from pydantic import BaseModel
from typing import Optional

class UserPreferences(BaseModel):
    temperature_unit: str = "Celsius"
    volume_unit: str = "liters"
    time_zone: str = "UTC"
    notification_sound: Optional[str] = "default"
