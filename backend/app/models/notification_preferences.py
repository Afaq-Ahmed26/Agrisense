from pydantic import BaseModel
from typing import Literal

NotificationChannel = Literal['in_app', 'email', 'none']

class NotificationPreferences(BaseModel):
    on_critical_alert: NotificationChannel = 'email'
    on_high_alert: NotificationChannel = 'in_app'
    on_medium_alert: NotificationChannel = 'in_app'
    on_low_alert: NotificationChannel = 'none'
