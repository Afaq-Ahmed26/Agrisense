from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: str
    username: str
    role: str = "farmer"  # Default role is farmer


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None


class User(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False # Added for soft deletion
    deleted_at: Optional[datetime] = None # Added for soft deletion

    class Config:
        from_attributes = True