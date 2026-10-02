from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
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
        status=order_data.status,
    )
    db.add(new_order)
    db.flush()  # Gera o ID do pedido antes de inserir os itens

    # Validar produtos e vincular itens
    for item in order_data.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto ID {item.product_id} não encontrado.",
            )

        order_item = models.OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
        )
        db.add(order_item)

    db.commit()
    db.refresh(new_order)
    return new_order


@router.get("/", response_model=List[schemas.OrderResponse])
def list_orders(
    order_type: Optional[str] = Query(
        None, alias="type", description="Filtra por tipo (INBOUND, OUTBOUND)"
    ),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filtra por status (PENDING, PROCESSING, etc.)"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(models.Order)
    if order_type:
        query = query.filter(models.Order.type == order_type)
    if status_filter:
        query = query.filter(models.Order.status == status_filter)
    return query.offset(skip).limit(limit).all()


@router.get("/{order_id}", response_model=schemas.OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado."
        )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado."
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado."
        )

    db.delete(db_order)
    db.commit()
    return None


# --- GERENCIAMENTO DE ITENS DO PEDIDO ---


@router.post(
    "/{order_id}/items",
    response_model=schemas.OrderItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_order_item(
    order_id: int,
    item: schemas.OrderItemCreate,
    db: Session = Depends(get_db),
    _: models.User = _write,
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado."
        )

    product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Produto ID {item.product_id} não encontrado.",
        )

    # Verifica se já existe o mesmo produto no pedido
    existing_item = (
        db.query(models.OrderItem)
        .filter(
            models.OrderItem.order_id == order_id,
            models.OrderItem.product_id == item.product_id,
        )
        .first()
    )

    if existing_item:
        existing_item.quantity += item.quantity
        db.commit()
        db.refresh(existing_item)
        return existing_item

    new_item = models.OrderItem(
        order_id=order_id, product_id=item.product_id, quantity=item.quantity
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.put("/{order_id}/items/{item_id}", response_model=schemas.OrderItemResponse)
def update_order_item(
    order_id: int,
    item_id: int,
    item_update: schemas.OrderItemUpdate,
    db: Session = Depends(get_db),
    _: models.User = _write,
):
    db_item = (
        db.query(models.OrderItem)
        .filter(
            models.OrderItem.id == item_id,
            models.OrderItem.order_id == order_id,
        )
        .first()
    )

    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item não encontrado no pedido informado.",
        )

    db_item.quantity = item_update.quantity
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{order_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order_item(
    order_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    _: models.User = _write,
):
    db_item = (
        db.query(models.OrderItem)
        .filter(
            models.OrderItem.id == item_id,
            models.OrderItem.order_id == order_id,
        )
        .first()
    )

    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item não encontrado no pedido informado.",
        )

    # Validação da regra de negócio: não remover o último item
    total_items = (
        db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).count()
    )
    if total_items <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível remover o último item. Um pedido deve conter ao menos um item. Cancele ou delete o pedido se necessário.",
        )

    db.delete(db_item)
    db.commit()
    return None