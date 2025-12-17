from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = None
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class SessionResponse(BaseModel):
    session_id: str
    device_name: str | None
    ip_address: str | None
    user_agent: str | None
    created: datetime
    expires_at: datetime | None
    is_active: bool

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str | None
    is_verified: bool
    is_active: bool

    class Config:
        from_attributes = True
