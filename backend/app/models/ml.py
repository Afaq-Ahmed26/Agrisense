from pydantic import BaseModel
from typing import Optional

class MLPredictionInput(BaseModel):
    soil_moisture: float
    temperature: float
    humidity: float
    light_level: float
    device_id: Optional[str] = None
