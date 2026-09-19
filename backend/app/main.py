from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import engine, Base
from .routers import auth, products, tasks, optimization, orders, stock, users, locations
from .routes.optimization import router as optimization_engine_router

# Inicializa as tabelas no PostgreSQL
Base.metadata.create_all(bind=engine)

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT_DIR / "frontend"

app = FastAPI(
    title="WarehouseFlow API",
    description="API inteligente para gerenciamento e otimização de operações em armazéns.",
    version="1.0.0",
)

# Registro de todas as rotas modularizadas (CRUD + persistência)
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(tasks.router)
app.include_router(optimization.router)
app.include_router(orders.router)
app.include_router(stock.router)
app.include_router(users.router)
app.include_router(locations.router)

# Motor de otimização de picking (desacoplado do PostgreSQL nesta versão)
app.include_router(optimization_engine_router)

# Frontend estático
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")
    templates = Jinja2Templates(directory=str(FRONTEND_DIR / "templates"))

    @app.get("/login", response_class=HTMLResponse, tags=["Frontend"])
    def login_page(request: Request):
        return templates.TemplateResponse("auth/login.html", {"request": request})


@app.get("/", tags=["Healthcheck"])
def healthcheck():
    return {"status": "ok", "message": "WarehouseFlow API operando normalmente!"}


@app.get("/health", tags=["Healthcheck"])
def health() -> dict[str, str]:
    return {"status": "ok"}