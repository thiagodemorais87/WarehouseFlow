from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ..models.user import UserRole

__all__ = [
    "UserRole",
    "LoginRequest",
    "TokenResponse",
    "AuthUserResponse",
]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthUserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: Optional[str] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)
