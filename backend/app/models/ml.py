from pydantic import BaseModel
from typing import Optional

class MLPredictionInput(BaseModel):
    soil_moisture: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    light_level: Optional[float] = None
    device_id: Optional[str] = None
