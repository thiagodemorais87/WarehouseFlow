from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas, database

# Cria as tabelas no banco caso não utilize Alembic no início
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="WarehouseFlow API")

@app.post("/products/", response_model=schemas.ProductResponse, tags=["Products"])
def create_product(product: schemas.ProductCreate, db: Session = Depends(database.get_db)):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/", response_model=list[schemas.ProductResponse], tags=["Products"])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products