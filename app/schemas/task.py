from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    total_minutes: Optional[int] = 0
    assigned_to: Optional[int] = None  # user_id to assign to; defaults to current user


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    total_minutes: Optional[int] = None


class TaskUpdateStatus(BaseModel):
    status: str


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    total_minutes: int
    user_id: int
    assigned_to: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True