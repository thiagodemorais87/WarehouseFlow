from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    GESTOR = "GESTOR"
    OPERADOR = "OPERADOR"


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
