from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TaskUpdateStatus(BaseModel):
    status: str


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    total_minutes: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True