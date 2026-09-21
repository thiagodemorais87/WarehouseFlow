"""Constantes de perfil RBAC (nomes alinhados à tabela `roles`)."""

from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    GESTOR = "GESTOR"
    OPERADOR = "OPERADOR"


__all__ = ["UserRole"]
