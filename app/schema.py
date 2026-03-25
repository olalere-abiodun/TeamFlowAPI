from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl, Field
from enum import Enum
from typing import Optional
from datetime import datetime, date, timedelta

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = Field(default=None, max_length=255)

class UserInDB(UserBase):
    uid: str
    role: str = "user"
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CurrentUser(BaseModel):
    uid: str
    email: str | None = None
