from fastapi import FastAPI
from .database import engine, Base
from .routers import products, tasks, optimization, orders, stock, users, locations

# Inicializa as tabelas no PostgreSQL
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WarehouseFlow API",
    description="API inteligente para gerenciamento e otimização de operações em armazéns.",
    version="1.0.0"
)

# Registro de todas as rotas modularizadas
app.include_router(products.router)
app.include_router(tasks.router)
app.include_router(optimization.router)
app.include_router(orders.router)
app.include_router(stock.router)
app.include_router(users.router)
app.include_router(locations.router)

@app.get("/", tags=["Healthcheck"])
def healthcheck():
    return {"status": "ok", "message": "WarehouseFlow API operando normalmente!"}