from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl, Field
from enum import Enum
from typing import Optional
from datetime import datetime, date, timedelta

class UserRole(str, Enum):
    USER = "user"
    OWNER = "owner"


class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = Field(default=None, max_length=255)

class UserInDB(UserBase):
    uid: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CurrentUser(BaseModel):
    uid: str
    email: str | None = None

class createOrganization(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UpdateOrganization(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    
class OrganizationResponce(BaseModel):
    name: str
    description: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
    
