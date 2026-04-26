from pydantic import BaseModel, field_validator, EmailStr, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
import re


class UserBase(BaseModel):
    email: str
    username: str
    role: str = "farmer"  # Default role is farmer
    full_name: Optional[str] = None
    dashboard_preferences: Optional[List[Dict[str, Any]]] = None
    assigned_device_ids: List[str] = Field(default_factory=list)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError('Invalid email format')
        return v.lower()


class UserCreate(UserBase):
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    dashboard_preferences: Optional[List[Dict[str, Any]]] = None
    assigned_device_ids: Optional[List[str]] = None
    is_active: Optional[bool] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
                raise ValueError('Invalid email format')
            return v.lower()
        return v


class User(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True  # Users are active by default
    is_deleted: bool = False # Added for soft deletion
    deleted_at: Optional[datetime] = None # Added for soft deletion
    dashboard_preferences: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True
