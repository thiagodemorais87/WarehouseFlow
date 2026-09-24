from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from .. import models, schemas
from ..deps import get_current_user, require_role
from ..models.user import UserRole

router = APIRouter(
    prefix="/locations",
    tags=["Warehouses & Locations"],
    dependencies=[Depends(get_current_user)],
)

_write = Depends(require_role(UserRole.ADMIN, UserRole.GESTOR))


#  WAREHOUSES 

@router.post("/warehouses/", response_model=schemas.WarehouseResponse, status_code=status.HTTP_201_CREATED)
def create_warehouse(
    warehouse: schemas.WarehouseCreate,
    db: Session = Depends(get_db),
    _: models.User = _write,
):
    new_warehouse = models.Warehouse(**warehouse.model_dump())
    db.add(new_warehouse)
    db.commit()
    db.refresh(new_warehouse)
    return new_warehouse

@router.get("/warehouses/", response_model=List[schemas.WarehouseResponse])
def list_warehouses(db: Session = Depends(get_db)):
    return db.query(models.Warehouse).all()

#  LOCATIONS 

@router.post("/", response_model=schemas.LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(
    location: schemas.LocationCreate,
    db: Session = Depends(get_db),
    _: models.User = _write,
):
    warehouse = db.query(models.Warehouse).filter(models.Warehouse.id == location.warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Armazém não encontrado.")

    existing_code = db.query(models.Location).filter(models.Location.code == location.code).first()
    if existing_code:
        raise HTTPException(status_code=400, detail="Código de vaga/posição já cadastrado.")

    new_location = models.Location(**location.model_dump())
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    return new_location

@router.get("/", response_model=List[schemas.LocationResponse])
def list_locations(
    warehouse_id: Optional[int] = Query(None),
    aisle: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(models.Location)
    if warehouse_id:
        query = query.filter(models.Location.warehouse_id == warehouse_id)
    if aisle:
        query = query.filter(models.Location.aisle == aisle)
    if is_active is not None:
        query = query.filter(models.Location.is_active == is_active)

    return query.offset(skip).limit(limit).all()

@router.get("/{location_id}", response_model=schemas.LocationResponse)
def get_location(location_id: int, db: Session = Depends(get_db)):
    location = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Posição não encontrada.")
    return location

@router.put("/{location_id}", response_model=schemas.LocationResponse)
def update_location(
    location_id: int,
    location_update: schemas.LocationUpdate,
    db: Session = Depends(get_db),
    _: models.User = _write,
):
    db_location = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not db_location:
        raise HTTPException(status_code=404, detail="Posição não encontrada.")

    update_data = location_update.model_dump(exclude_unset=True)

    if "code" in update_data and update_data["code"] != db_location.code:
        existing = db.query(models.Location).filter(models.Location.code == update_data["code"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="Novo código de posição já em uso.")

    for key, value in update_data.items():
        setattr(db_location, key, value)

    db.commit()
    db.refresh(db_location)
    return db_location

@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    _: models.User = _write,
):
    db_location = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not db_location:
        raise HTTPException(status_code=404, detail="Posição não encontrada.")

    db.delete(db_location)
    db.commit()
    return None