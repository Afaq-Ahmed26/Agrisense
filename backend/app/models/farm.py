from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import json

from app.config import settings


class FarmBase(BaseModel):
    name: str
    owner_id: str  # User ID of the farmer who owns the farm
    assigned_officer_id: Optional[str] = None  # User ID of the officer assigned to this farm
    assigned_middleman_ids: List[str] = Field(default_factory=list)  # List of middleman/officer IDs with access
    device_ids: List[str] = Field(default_factory=list) # List of device IDs associated with this farm


class FarmCreate(FarmBase):
    pass


class FarmUpdate(BaseModel):
    name: Optional[str] = None
    assigned_officer_id: Optional[str] = None # Allows farmer/admin to assign/remove officer
    assigned_middleman_ids: Optional[List[str]] = None # Allows farmer/admin to manage middleman access
    device_ids: Optional[List[str]] = None # Allows farmer/admin to manage devices


class Farm(FarmBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
