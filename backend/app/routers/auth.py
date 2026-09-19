from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
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

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo. Entre em contato com o administrador."
        )

    # Gera o token carregando o ID e o Perfil (role) no payload
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )

    return {"access_token": access_token, "token_type": "bearer"}