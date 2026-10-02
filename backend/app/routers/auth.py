from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.user import LoginRequest, TokenResponse
from app.security import verify_password, create_access_token

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="Autenticar usuário")
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Realiza o login do usuário validando e-mail e senha.
    Retorna o Token JWT caso as credenciais estejam corretas.
    """
    user = db.query(User).filter(User.email == login_data.email).first()

    password_is_valid = False
    if user:
        try:
            password_is_valid = verify_password(login_data.password, user.password_hash)
        except (TypeError, ValueError):
            password_is_valid = False

    if not user or not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not getattr(user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo. Entre em contato com o administrador."
        )

    # Gera o token carregando o ID e o Perfil (role) no payload
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.name if user.role else "OPERATOR",
        }
    )

    return {"access_token": access_token, "token_type": "bearer"}