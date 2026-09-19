import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UserRole(str, enum.Enum):
    """
    Enumeração que define os perfis de acesso (RBAC) do sistema WarehouseFlow.
    """
    ADMIN = "ADMIN"
    GESTOR = "GESTOR"
    OPERADOR = "OPERADOR"


class User(Base):
    """
    Entidade de Usuário para autenticação e controle de acesso.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.OPERADOR, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"