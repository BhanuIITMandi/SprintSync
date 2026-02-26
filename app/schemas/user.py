from pydantic import BaseModel, EmailStr
from datetime import datetime


# Request → create user
class UserCreate(BaseModel):
    email: EmailStr
    password: str


# Response → send back to client
class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True