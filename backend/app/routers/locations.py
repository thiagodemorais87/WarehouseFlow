from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/locations",
    tags=["Warehouses & Locations"]
)


#  helpers

def _get_warehouse_or_404(db: Session, warehouse_id: int) -> models.Warehouse:
    warehouse = db.query(models.Warehouse).filter(models.Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Armazém não encontrado.")
    return warehouse


def _get_location_or_404(db: Session, location_id: int) -> models.Location:
    location = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Posição não encontrada.")
    return location


def _codigo_em_uso(db: Session, code: str, ignorar_id: Optional[int] = None) -> bool:
    query = db.query(models.Location.id).filter(models.Location.code == code)
    if ignorar_id is not None:
        query = query.filter(models.Location.id != ignorar_id)
    return query.first() is not None


@router.post("/warehouses", response_model=schemas.WarehouseResponse, status_code=status.HTTP_201_CREATED)
@router.post("/warehouses/", response_model=schemas.WarehouseResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_warehouse(warehouse: schemas.WarehouseCreate, db: Session = Depends(get_db)):
    new_warehouse = models.Warehouse(**warehouse.model_dump())
    db.add(new_warehouse)
    db.commit()
    db.refresh(new_warehouse)
    return new_warehouse


@router.get("/warehouses", response_model=List[schemas.WarehouseResponse])
@router.get("/warehouses/", response_model=List[schemas.WarehouseResponse], include_in_schema=False)
def list_warehouses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return db.query(models.Warehouse).order_by(models.Warehouse.id).offset(skip).limit(limit).all()


@router.get("/warehouses/{warehouse_id}", response_model=schemas.WarehouseResponse)
def get_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    return _get_warehouse_or_404(db, warehouse_id)


@router.put("/warehouses/{warehouse_id}", response_model=schemas.WarehouseResponse)
def update_warehouse(warehouse_id: int, warehouse_update: schemas.WarehouseUpdate, db: Session = Depends(get_db)):
    db_warehouse = _get_warehouse_or_404(db, warehouse_id)

    update_data = warehouse_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe ao menos um campo para atualizar.")

    for key, value in update_data.items():
        setattr(db_warehouse, key, value)

    db.commit()
    db.refresh(db_warehouse)
    return db_warehouse


@router.delete("/warehouses/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    db_warehouse = _get_warehouse_or_404(db, warehouse_id)

    # ON DELETE CASCADE apagaria posições e estoque em silêncio; exige esvaziar antes.
    total = db.query(models.Location).filter(models.Location.warehouse_id == warehouse_id).count()
    if total > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Não é possível excluir o armazém: existem {total} posição(ões) cadastrada(s) nele. "
                   "Exclua ou mova as posições antes."
        )

    db.delete(db_warehouse)
    db.commit()
    return None


#  LOCATIONS

@router.post("", response_model=schemas.LocationResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=schemas.LocationResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_location(location: schemas.LocationCreate, db: Session = Depends(get_db)):
    _get_warehouse_or_404(db, location.warehouse_id)

    if _codigo_em_uso(db, location.code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe uma posição cadastrada com o código '{location.code}'."
        )

    new_location = models.Location(**location.model_dump())
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    return new_location


@router.get("", response_model=List[schemas.LocationResponse])
@router.get("/", response_model=List[schemas.LocationResponse], include_in_schema=False)
def list_locations(
    warehouse_id: Optional[int] = Query(None),
    aisle: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(models.Location)
    if warehouse_id is not None:
        query = query.filter(models.Location.warehouse_id == warehouse_id)
    if aisle:
        query = query.filter(models.Location.aisle == aisle)
    if is_active is not None:
        query = query.filter(models.Location.is_active == is_active)

    return query.order_by(models.Location.id).offset(skip).limit(limit).all()


@router.get("/{location_id:int}", response_model=schemas.LocationResponse)
def get_location(location_id: int, db: Session = Depends(get_db)):
    return _get_location_or_404(db, location_id)


@router.put("/{location_id:int}", response_model=schemas.LocationResponse)
def update_location(location_id: int, location_update: schemas.LocationUpdate, db: Session = Depends(get_db)):
    db_location = _get_location_or_404(db, location_id)

    update_data = location_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe ao menos um campo para atualizar.")

    if "warehouse_id" in update_data:
        _get_warehouse_or_404(db, update_data["warehouse_id"])

    if "code" in update_data and update_data["code"] != db_location.code:
        if _codigo_em_uso(db, update_data["code"], ignorar_id=location_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"O código '{update_data['code']}' já está em uso por outra posição."
            )

    for key, value in update_data.items():
        setattr(db_location, key, value)

    db.commit()
    db.refresh(db_location)
    return db_location


@router.delete("/{location_id:int}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(location_id: int, db: Session = Depends(get_db)):
    db_location = _get_location_or_404(db, location_id)

    unidades = (
        db.query(func.coalesce(func.sum(models.Stock.quantity), 0))
        .filter(models.Stock.location_id == location_id)
        .scalar()
    )
    if unidades > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Não é possível excluir a posição: há {unidades} unidade(s) em estoque nela. "
                   "Transfira ou zere o estoque antes."
        )

    sugestoes = (
        db.query(models.OptimizationResult)
        .filter(models.OptimizationResult.suggested_location_id == location_id)
        .count()
    )
    if sugestoes > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Não é possível excluir a posição: ela é referenciada por {sugestoes} resultado(s) de otimização. "
                   "Desative a posição (is_active=false) em vez de excluí-la."
        )

    db.delete(db_location)  # registros de estoque com quantidade 0 saem por cascade
    db.commit()
    return None