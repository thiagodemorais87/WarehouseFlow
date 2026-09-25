from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import engine, Base
from .routers import auth, products, tasks, optimization, orders, stock, users, locations
from .routers.optimization_engine import router as optimization_engine_router


# Inicializa as tabelas no PostgreSQL
Base.metadata.create_all(bind=engine)

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", str(ROOT_DIR / "frontend"))).resolve()


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

# Frontend Jinja (login, dashboard, produtos, estoque, posições)
if FRONTEND_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(FRONTEND_DIR / "static")),
        name="static",
    )

    templates = Jinja2Templates(
        directory=str(FRONTEND_DIR / "templates")
    )

    @app.get(
        "/login",
        response_class=HTMLResponse,
        tags=["Frontend"],
    )
    def login_page(request: Request):
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={},
        )

    @app.get(
        "/dashboard",
        response_class=HTMLResponse,
        tags=["Frontend"],
    )
    def dashboard_page(request: Request):
        user = {
            "name": "Usuário Teste",
            "initials": "UT",
            "role": "Administrador",
        }

        return templates.TemplateResponse(
            request=request,
            name="dashboard/dashboard.html",
            context={
                "user": user,
                "active_page": "dashboard",
            },
        )

    @app.get(
        "/produtos",
        response_class=HTMLResponse,
        tags=["Frontend"],
    )
    def products_page(request: Request):
        user = {
            "name": "Usuário Teste",
            "initials": "UT",
            "role": "Administrador",
        }

        return templates.TemplateResponse(
            request=request,
            name="products/products.html",
            context={
                "user": user,
                "active_page": "products",
            },
        )

    @app.get(
        "/estoque",
        response_class=HTMLResponse,
        tags=["Frontend"],
    )
    def stock_page(request: Request):
        user = {
            "name": "Usuário Teste",
            "initials": "UT",
            "role": "Administrador",
        }

        return templates.TemplateResponse(
            request=request,
            name="inventory/stock.html",
            context={
                "user": user,
                "active_page": "stock",
            },
        )

    @app.get(
        "/posicoes",
        response_class=HTMLResponse,
        tags=["Frontend"],
    )
    def locations_page(request: Request):
        user = {
            "name": "Usuário Teste",
            "initials": "UT",
            "role": "Administrador",
        }

        return templates.TemplateResponse(
            request=request,
            name="locations/locations.html",
            context={
                "user": user,
                "active_page": "locations",
            },
        )
else:
    logger.warning(
        "FRONTEND_DIR não encontrado em %s — rotas HTML (/login, /dashboard, …) não serão registradas.",
        FRONTEND_DIR,
    )


@app.get("/", include_in_schema=False)
def root():
    """Entrada da UI: redireciona para o login do frontend."""
    return RedirectResponse(url="/login", status_code=302)


@app.get("/health", tags=["Healthcheck"])
def health() -> dict[str, str]:
    return {"status": "ok"}
