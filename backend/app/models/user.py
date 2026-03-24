from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class UserBase(BaseModel):
    email: str
    username: str
    role: str = "farmer"  # Default role is farmer
    full_name: Optional[str] = None
    dashboard_preferences: Optional[Dict] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    dashboard_preferences: Optional[list[dict]] = None
    is_active: Optional[bool] = None


class User(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True  # Users are active by default
    is_deleted: bool = False # Added for soft deletion
    deleted_at: Optional[datetime] = None # Added for soft deletion
    dashboard_preferences: Optional[list[dict]] = None

    class Config:
        from_attributes = True