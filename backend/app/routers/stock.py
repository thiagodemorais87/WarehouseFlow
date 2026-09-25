from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_role
from ..models.user import UserRole

router = APIRouter(
    prefix="/stock",
    tags=["Stock"],
    dependencies=[Depends(get_current_user)],
)

# OPERADOR pode movimentar estoque; exclusão restrita
_manage = Depends(require_role(UserRole.ADMIN, UserRole.GESTOR, UserRole.OPERADOR))
_admin_gestor = Depends(require_role(UserRole.ADMIN, UserRole.GESTOR))


#  helpers

def _get_stock_or_404(db: Session, stock_id: int, for_update: bool = False) -> models.Stock:
    query = db.query(models.Stock).filter(models.Stock.id == stock_id)
    if for_update:
        query = query.with_for_update()  # evita perda de atualização em saídas simultâneas
    stock = query.first()
    if not stock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de estoque não encontrado.")
    return stock


def _validar_produto_e_posicao(db: Session, product_id: int, location_id: int) -> models.Location:
    if not db.query(models.Product.id).filter(models.Product.id == product_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")

    location = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Posição do armazém não encontrada.")
    return location


def _exigir_posicao_ativa(location: models.Location) -> None:
    if not location.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A posição '{location.code}' está inativa e não pode receber estoque."
        )


def _exigir_limite(quantidade: int) -> None:
    if quantidade > schemas.MAX_QUANTITY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A quantidade resultante excede o limite permitido ({schemas.MAX_QUANTITY})."
        )


# CRUD

@router.post("", response_model=schemas.StockResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=schemas.StockResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_stock(
    stock_data: schemas.StockCreate,
    db: Session = Depends(get_db),
    _: models.User = _manage,
):
    """Cria o saldo de um produto em uma posição. Para alterar um saldo existente use PUT ou /inbound."""
    location = _validar_produto_e_posicao(db, stock_data.product_id, stock_data.location_id)
    _exigir_posicao_ativa(location)

    existente = db.query(models.Stock).filter(
        models.Stock.product_id == stock_data.product_id,
        models.Stock.location_id == stock_data.location_id,
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe estoque deste produto na posição '{location.code}' (registro {existente.id}). "
                   f"Use PUT /stock/{existente.id} para definir a quantidade ou "
                   f"POST /stock/{existente.id}/inbound para somar."
        )

    db_stock = models.Stock(**stock_data.model_dump())
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock


@router.get("", response_model=List[schemas.StockResponse])
@router.get("/", response_model=List[schemas.StockResponse], include_in_schema=False)
def list_stock(
    product_id: Optional[int] = Query(None),
    location_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(models.Stock)
    if product_id is not None:
        query = query.filter(models.Stock.product_id == product_id)
    if location_id is not None:
        query = query.filter(models.Stock.location_id == location_id)
    return query.order_by(models.Stock.id).offset(skip).limit(limit).all()


@router.get("/{stock_id}", response_model=schemas.StockResponse)
def get_stock_by_id(stock_id: int, db: Session = Depends(get_db)):
    return _get_stock_or_404(db, stock_id)


@router.put("/{stock_id}", response_model=schemas.StockResponse)
def update_stock_quantity(
    stock_id: int,
    stock_update: schemas.StockUpdate,
    db: Session = Depends(get_db),
    _: models.User = _manage,
):
    """Define a quantidade total (ajuste/inventário). Não altera produto nem posição."""
    db_stock = _get_stock_or_404(db, stock_id, for_update=True)
    db_stock.quantity = stock_update.quantity
    db.commit()
    db.refresh(db_stock)
    return db_stock


@router.delete("/{stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stock(
    stock_id: int,
    db: Session = Depends(get_db),
    _: models.User = _admin_gestor,
):
    db_stock = _get_stock_or_404(db, stock_id)
    db.delete(db_stock)
    db.commit()
    return None


# ENTRADAS E SAÍDAS

@router.post("/{stock_id}/inbound", response_model=schemas.StockResponse)
def stock_inbound(
    stock_id: int,
    movement: schemas.StockMovement,
    db: Session = Depends(get_db),
    _: models.User = _manage,
):
    """Entrada: soma a quantidade ao saldo existente."""
    db_stock = _get_stock_or_404(db, stock_id, for_update=True)
    _exigir_posicao_ativa(db_stock.location)

    nova_quantidade = db_stock.quantity + movement.quantity
    _exigir_limite(nova_quantidade)

    db_stock.quantity = nova_quantidade
    db.commit()
    db.refresh(db_stock)
    return db_stock


@router.post("/{stock_id}/outbound", response_model=schemas.StockResponse)
def stock_outbound(
    stock_id: int,
    movement: schemas.StockMovement,
    db: Session = Depends(get_db),
    _: models.User = _manage,
):
    """Saída: subtrai do saldo. Nunca permite quantidade negativa."""
    db_stock = _get_stock_or_404(db, stock_id, for_update=True)

    if movement.quantity > db_stock.quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Estoque insuficiente: disponível {db_stock.quantity} unidade(s), "
                   f"solicitado {movement.quantity}."
        )

    db_stock.quantity -= movement.quantity
    db.commit()
    db.refresh(db_stock)
    return db_stock
