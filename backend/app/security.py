import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from dotenv import load_dotenv
from jose import jwt

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development").strip().lower() or "development"

_WEAK_SECRET_PLACEHOLDERS = {
    "",
    "altere-esta-chave-em-desenvolvimento",
    "SUBSTITUA_POR_UMA_CHAVE_SECRETA_ALEATORIA",
    "SUBSTITUA_POR_UMA_CHAVE_SECRETA_ALEATORIA_LONGA",
    "change-me",
    "secret",
    "test-secret",
}

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("A variável SECRET_KEY não foi encontrada no arquivo .env")

if APP_ENV in {"staging", "production"}:
    if SECRET_KEY.strip() in _WEAK_SECRET_PLACEHOLDERS or len(SECRET_KEY.strip()) < 32:
        raise ValueError(
            "SECRET_KEY fraca ou placeholder detectada. "
            "Em staging/produção use uma chave aleatória com pelo menos 32 caracteres."
        )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas de validade

COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() in ("1", "true", "yes")
COOKIE_SAMESITE = "lax"
COOKIE_HTTPONLY = True


def hash_password(password: str) -> str:
    """Gera o hash seguro da senha fornecida em texto puro."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha fornecida no login bate com o hash armazenado."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria o token JWT com os dados do usuário e uma data de validade."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
