from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from .. import models, schemas

router = APIRouter(
    prefix="/stock",
    tags=["Stock"]
)

@router.post("/", response_model=schemas.StockResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_stock(stock_data: schemas.StockCreate, db: Session = Depends(get_db)):
    # Validar existência do produto e da vaga
    product = db.query(models.Product).filter(models.Product.id == stock_data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    
    location = db.query(models.Location).filter(models.Location.id == stock_data.location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Posição do armazém não encontrada.")

    # Se já existir o par (produto, posição), incrementa a quantidade (Upsert)
    db_stock = db.query(models.Stock).filter(
        models.Stock.product_id == stock_data.product_id,
        models.Stock.location_id == stock_data.location_id
    ).first()

    if db_stock:
        db_stock.quantity += stock_data.quantity
    else:
        db_stock = models.Stock(**stock_data.model_dump())
        db.add(db_stock)

    db.commit()
    db.refresh(db_stock)
    return db_stock

@router.get("/", response_model=List[schemas.StockResponse])
def list_stock(product_id: Optional[int] = None, location_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(models.Stock)
    if product_id:
        query = query.filter(models.Stock.product_id == product_id)
    if location_id:
        query = query.filter(models.Stock.location_id == location_id)
    return query.offset(skip).limit(limit).all()

@router.get("/{stock_id}", response_model=schemas.StockResponse)
def get_stock_by_id(stock_id: int, db: Session = Depends(get_db)):
    stock_item = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    if not stock_item:
        raise HTTPException(status_code=404, detail="Registro de estoque não encontrado.")
    return stock_item

@router.put("/{stock_id}", response_model=schemas.StockResponse)
def update_stock_quantity(stock_id: int, stock_update: schemas.StockUpdate, db: Session = Depends(get_db)):
    db_stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    if not db_stock:
        raise HTTPException(status_code=404, detail="Registro de estoque não encontrado.")

    db_stock.quantity = stock_update.quantity
    db.commit()
    db.refresh(db_stock)
    return db_stock

@router.delete("/{stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stock(stock_id: int, db: Session = Depends(get_db)):
    db_stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    if not db_stock:
        raise HTTPException(status_code=404, detail="Registro de estoque não encontrado.")

    db.delete(db_stock)
    db.commit()
    return None