from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from .. import models, schemas
from ..deps import get_current_user, require_role
from ..models.user import UserRole

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
    dependencies=[Depends(get_current_user)],
)

_write = Depends(require_role(UserRole.ADMIN, UserRole.GESTOR, UserRole.OPERADOR))


@router.post("/", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    _: models.User = _write,
):
    # Valida se o pedido vinculado existe
    order = db.query(models.Order).filter(models.Order.id == task.order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Pedido de ID {task.order_id} não encontrado."
        )
    
    # Valida o operador se informado
    if task.assigned_user_id:
        user = db.query(models.User).filter(models.User.id == task.assigned_user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Usuário de ID {task.assigned_user_id} não encontrado."
            )
        
    new_task = models.Task(**task.model_dump())
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@router.get("/", response_model=List[schemas.TaskResponse])
def list_tasks(
    task_type: Optional[str] = Query(None, alias="type", description="Filtra por tipo (PICKING, PUTAWAY, etc.)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filtra por status (PENDING, IN_PROGRESS, etc.)"),
    assigned_user_id: Optional[int] = Query(None, description="Filtra por operador atribuído"),
    order_id: Optional[int] = Query(None, description="Filtra tarefas de um pedido específico"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(models.Task)
    
    if task_type:
        query = query.filter(models.Task.type == task_type)
    if status_filter:
        query = query.filter(models.Task.status == status_filter)
    if assigned_user_id:
        query = query.filter(models.Task.assigned_user_id == assigned_user_id)
    if order_id:
        query = query.filter(models.Task.order_id == order_id)
        
    return query.offset(skip).limit(limit).all()

@router.get("/{task_id}", response_model=schemas.TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada.")
    return task

@router.put("/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    _: models.User = _write,
):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada.")
    
    update_data = task_update.model_dump(exclude_unset=True)
    
    if "assigned_user_id" in update_data and update_data["assigned_user_id"] is not None:
        user = db.query(models.User).filter(models.User.id == update_data["assigned_user_id"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Usuário operador atribuído não foi encontrado."
            )

    for key, value in update_data.items():
        setattr(db_task, key, value)
        
    db.commit()
    db.refresh(db_task)
    return db_task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role(UserRole.ADMIN, UserRole.GESTOR)),
):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada.")
    
    db.delete(db_task)
    db.commit()
    return None