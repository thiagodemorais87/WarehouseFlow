from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from .. import models, schemas
from ..deps import get_current_user, require_role
from ..models.user import UserRole

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
    dependencies=[Depends(get_current_user)],
)

_write = Depends(require_role(UserRole.ADMIN, UserRole.GESTOR, UserRole.OPERADOR))


@router.post("/", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: schemas.OrderCreate,
    db: Session = Depends(get_db),
    _: models.User = _write,
):
    # Criar registro principal do Pedido
    new_order = models.Order(
        type=order_data.type,
        status=order_data.status
    )
    db.add(new_order)
    db.flush()  # Gera o ID do pedido antes de inserir os itens

    # Validar produtos e vincular itens
    for item in order_data.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Produto ID {item.product_id} não encontrado.")
        
        order_item = models.OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(order_item)

    db.commit()
    db.refresh(new_order)
    return new_order

@router.get("/", response_model=List[schemas.OrderResponse])
def list_orders(type: Optional[str] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(models.Order)
    if type:
        query = query.filter(models.Order.type == type)
    if status:
        query = query.filter(models.Order.status == status)
    return query.offset(skip).limit(limit).all()

@router.get("/{order_id}", response_model=schemas.OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    return order

@router.put("/{order_id}", response_model=schemas.OrderResponse)
def update_order(
    order_id: int,
    order_update: schemas.OrderUpdate,
    db: Session = Depends(get_db),
    _: models.User = _write,
):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    
    update_data = order_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_order, key, value)

    db.commit()
    db.refresh(db_order)
    return db_order

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role(UserRole.ADMIN, UserRole.GESTOR)),
):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    
    db.delete(db_order)
    db.commit()
    return None