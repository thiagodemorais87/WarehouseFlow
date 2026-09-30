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

# POST /orders/{id}/items
@router.post("/{order_id}/items", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
def add_item_to_order(
    order_id: int,
    item_data: schemas.OrderItemCreate,
    db: Session = Depends(get_db),
    _: models.User = _write,
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    
    product = db.query(models.Product).filter(models.Product.id == item_data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Produto ID {item_data.product_id} não encontrado.")

    # Se o item já existir no pedido, incrementa a quantidade, caso contrário cria um novo
    existing_item = db.query(models.OrderItem).filter(
        models.OrderItem.order_id == order_id,
        models.OrderItem.product_id == item_data.product_id
    ).first()

    if existing_item:
        existing_item.quantity += item_data.quantity
    else:
        new_item = models.OrderItem(
            order_id=order_id,
            product_id=item_data.product_id,
            quantity=item_data.quantity
        )
        db.add(new_item)

    db.commit()
    db.refresh(order)
    return order


# PUT /orders/{id}/items/{product_id}
@router.put("/{order_id}/items/{product_id}", response_model=schemas.OrderResponse)
def update_order_item(
    order_id: int,
    product_id: int,
    item_update: schemas.OrderItemUpdate,
    db: Session = Depends(get_db),
    _: models.User = _write,
):
    item = db.query(models.OrderItem).filter(
        models.OrderItem.order_id == order_id,
        models.OrderItem.product_id == product_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item do pedido não encontrado.")

    item.quantity = item_update.quantity
    db.commit()

    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    db.refresh(order)
    return order


# DELETE /orders/{id}/items/{product_id}
@router.delete("/{order_id}/items/{product_id}", response_model=schemas.OrderResponse)
def remove_order_item(
    order_id: int,
    product_id: int,
    db: Session = Depends(get_db),
    _: models.User = _write,
):
    item = db.query(models.OrderItem).filter(
        models.OrderItem.order_id == order_id,
        models.OrderItem.product_id == product_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item do pedido não encontrado.")

    # Garante que o pedido não fique sem itens se for regra de negócio
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if len(order.items) <= 1:
        raise HTTPException(status_code=400, detail="O pedido deve conter pelo menos um item.")

    db.delete(item)
    db.commit()
    db.refresh(order)
    return order