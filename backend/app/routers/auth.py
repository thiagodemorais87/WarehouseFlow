from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas.user import AuthUserResponse, LoginRequest, TokenResponse
from ..security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, verify_password


router = APIRouter(prefix="/auth", tags=["Auth"])


def _authenticate(db: Session, email: str, password: str, response: Response) -> dict:
    """Valida credenciais, grava o cookie e devolve o token (compartilhado por /login e /token)."""
    user = (
        db.query(User)
        .options(joinedload(User.role))
        .filter(User.email == email)
        .first()
    )

    password_is_valid = False
    if user:
        try:
            password_is_valid = verify_password(password, user.password_hash)
        except (TypeError, ValueError):
            password_is_valid = False

    if not user or not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not getattr(user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo. Entre em contato com o administrador.",
        )

    if user.role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário sem perfil de acesso",
        )

    role_name = user.role_name or "OPERADOR"
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": role_name}
    )

    # Grava o token também em cookie, para o servidor reconhecer o usuário nas páginas HTML
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse, summary="Autenticar usuário")
def login(login_data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """
    Realiza o login do usuário validando e-mail e senha (JSON).
    Retorna o Token JWT caso as credenciais estejam corretas.
    """
    return _authenticate(db, login_data.email, login_data.password, response)


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Token OAuth2 (botão Authorize do Swagger)",
)
def token(
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Mesmo login de `/auth/login`, mas no formato form-data do OAuth2.

    No Swagger, clique em **Authorize** e use o e-mail no campo *username*.
    """
    return _authenticate(db, form.username.strip(), form.password, response)


@router.get("/me", response_model=AuthUserResponse, summary="Usuário autenticado")
def me(current_user: User = Depends(get_current_user)):
    """Devolve o usuário logado; a tela usa isso para saber o perfil."""
    return AuthUserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role_name,
        is_active=current_user.is_active,
    )