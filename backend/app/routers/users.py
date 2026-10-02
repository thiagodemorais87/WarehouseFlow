from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..security import hash_password
from ..deps import get_current_user, require_role
from ..models.user import UserRole

router = APIRouter(
    prefix="/users",
    tags=["Users & Roles"],
    dependencies=[Depends(get_current_user)],
)

_admin = Depends(require_role(UserRole.ADMIN))


# --- ROLES ---

@router.post("/roles/", response_model=schemas.RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    role: schemas.RoleCreate,
    db: Session = Depends(get_db),
    _: models.User = _admin,
):
    db_role = db.query(models.Role).filter(models.Role.name == role.name.upper()).first()
    if db_role:
        raise HTTPException(status_code=400, detail="Cargo já cadastrado.")
    
    new_role = models.Role(name=role.name.upper())
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role


@router.get("/roles/", response_model=List[schemas.RoleResponse])
def list_roles(db: Session = Depends(get_db)):
    return db.query(models.Role).all()


# --- USERS ---

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    _: models.User = _admin,
):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="E-mail já está em uso.")

    if user.role_id:
        role = db.query(models.Role).filter(models.Role.id == user.role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role não encontrada.")

    # Criptografia real usando passlib/bcrypt
    hashed_password = hash_password(user.password)

    user_data = user.model_dump(exclude={"password"})
    new_user = models.User(**user_data, password_hash=hashed_password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/", response_model=List[schemas.UserResponse])
def list_users(
    role_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(models.User)
    if role_id:
        query = query.filter(models.User.role_id == role_id)
    return query.offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user


@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    _: models.User = _admin,
):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    update_data = user_update.model_dump(exclude_unset=True)

    if "password" in update_data:
        # Atualização com criptografia real
        update_data["password_hash"] = hash_password(update_data.pop("password"))

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: models.User = _admin,
):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    db.delete(db_user)
    db.commit()
    return None