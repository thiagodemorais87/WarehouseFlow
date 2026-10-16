from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from .. import models, schemas
from ..deps import get_current_user, require_role
from ..models.user import UserRole

router = APIRouter(
    prefix="/optimization-results",
    tags=["Optimization"],
    dependencies=[Depends(get_current_user)],
)

_write = Depends(require_role(UserRole.ADMIN, UserRole.GESTOR, UserRole.OPERADOR))


@router.post("/", response_model=schemas.OptimizationResultResponse, status_code=status.HTTP_201_CREATED)
def save_optimization_result(
    result: schemas.OptimizationResultCreate,
    db: Session = Depends(get_db),
    _: models.User = _write,
):
    # Valida se a tarefa vinculada existe
    task = db.query(models.Task).filter(models.Task.id == result.task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Tarefa de ID {result.task_id} não encontrada."
        )
        
    # Valida a posição sugerida se informada
    if result.suggested_location_id:
        location = db.query(models.Location).filter(models.Location.id == result.suggested_location_id).first()
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Posição de ID {result.suggested_location_id} não encontrada."
            )

    new_result = models.OptimizationResult(**result.model_dump())
    db.add(new_result)
    db.commit()
    db.refresh(new_result)
    return new_result

@router.get("/", response_model=List[schemas.OptimizationResultResponse])
def list_optimization_results(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    return db.query(models.OptimizationResult).offset(skip).limit(limit).all()

@router.get("/{result_id}", response_model=schemas.OptimizationResultResponse)
def get_optimization_result(result_id: int, db: Session = Depends(get_db)):
    result = db.query(models.OptimizationResult).filter(models.OptimizationResult.id == result_id).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Resultado de otimização não encontrado."
        )
    return result

@router.get("/task/{task_id}", response_model=List[schemas.OptimizationResultResponse])
def get_optimization_by_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Tarefa de ID {task_id} não encontrada."
        )
        
    return db.query(models.OptimizationResult).filter(
        models.OptimizationResult.task_id == task_id
    ).order_by(models.OptimizationResult.created_at.desc()).all()

@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_optimization_result(
    result_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role(UserRole.ADMIN, UserRole.GESTOR)),
):
    result = db.query(models.OptimizationResult).filter(models.OptimizationResult.id == result_id).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Resultado de otimização não encontrado."
        )
    
    db.delete(result)
    db.commit()
    return None