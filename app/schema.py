from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl, Field
from enum import Enum
from typing import Optional
from datetime import datetime, date, timedelta

class UserRole(str, Enum):
    USER = "user"
    OWNER = "owner"
    ADMIN = "admin"

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


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
    
class InvitationCreate(BaseModel):
    organization_id: int
    email: EmailStr

class ProjectCreate(BaseModel):
    organization_id: int
    name: str
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class BoardCreate(BaseModel):
    project_id: int
    name: str
    description: Optional[str] = None

class TaskCreate(BaseModel):
    board_id: int
    title: str
    description: Optional[str] = None
    assignee_id: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[date] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[date] = None


