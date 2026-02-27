from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# Request → create user
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    skills: Optional[str] = None


# Response → send back to client
class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool
    skills: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True