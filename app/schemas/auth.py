from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class SignupRequest(BaseModel):
    email: EmailStr
    display_name: str


class LoginRequest(BaseModel):
    email: EmailStr


class MagicLinkVerifyRequest(BaseModel):
    token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class AuthResponse(BaseModel):
    message: str
    email: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    avatar_url: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True