from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import User
from app.models.user import UserRole
from app.security import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

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


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Extrai e valida o token JWT enviado no cabeçalho Authorization."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de autenticação inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as exc:
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


def require_role(*allowed_roles: UserRole):
    """Dependência que verifica se o perfil do usuário logado possui permissão."""
    allowed = {_normalize_role(r.value if isinstance(r, UserRole) else str(r)) for r in allowed_roles}

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = _normalize_role(current_user.role_name)
        if user_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: seu perfil não possui permissão para esta operação.",
            )
        return current_user

    return role_checker
