from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class UserRole:
    ADMIN = "admin"
    DOCTOR = "doctor"
    CODER = "coder"
    AUDITOR = "auditor"

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = Field(default=UserRole.DOCTOR, description="Role of the user in the system")
    is_active: bool = True
    consent_given: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: str = Field(alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class UserResponse(UserBase):
    id: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
