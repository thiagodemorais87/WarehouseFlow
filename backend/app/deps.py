from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session, joinedload

from .database import get_db
from .models import User
from .models.user import UserRole
from .security import ALGORITHM, SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# Compatibilidade com nomes antigos do seed (OPERATOR/MANAGER)
_ROLE_ALIASES = {
    "OPERATOR": UserRole.OPERADOR.value,
    "OPERADOR": UserRole.OPERADOR.value,
    "MANAGER": UserRole.GESTOR.value,
    "GESTOR": UserRole.GESTOR.value,
    "ADMIN": UserRole.ADMIN.value,
}


def _normalize_role(name: str | None) -> str | None:
    if not name:
        return None
    return _ROLE_ALIASES.get(name.upper(), name.upper())


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Lê o token (cabeçalho ou cookie), valida e devolve o usuário do banco."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = token or request.cookies.get("access_token")
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValueError) as exc:
        raise credentials_exception from exc

    user = (
        db.query(User)
        .options(joinedload(User.role))
        .filter(User.id == int(user_id))
        .first()
    )
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def get_current_user_or_none(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Versão para páginas: devolve o usuário logado ou None, sem levantar erro."""
    try:
        return get_current_user(request=request, token=None, db=db)
    except HTTPException:
        return None


def require_role(*allowed_roles: UserRole):
    """Dependência que verifica se o perfil do usuário logado possui permissão."""
    allowed = {
        _normalize_role(r.value if isinstance(r, UserRole) else str(r))
        for r in allowed_roles
    }

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = _normalize_role(current_user.role_name)
        if user_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: seu perfil não possui permissão para esta operação.",
            )
        return current_user

    return role_checker
