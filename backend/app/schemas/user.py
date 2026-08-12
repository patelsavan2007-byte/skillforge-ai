from typing import Optional
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    name: str
    email: str
    profile_picture: Optional[str] = ""

class UserCreate(UserBase):
    google_id: Optional[str] = ""

class UserResponse(UserBase):
    id: str
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
