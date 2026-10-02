from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import Base, engine
from .routers import (
    auth,
    locations,
    optimization,
    orders,
    products,
    stock,
    tasks,
    users,
)
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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    erros_formatados = []
    for erro in exc.errors():
        campo = " -> ".join([str(loc) for loc in erro["loc"] if loc not in ("body", "query", "path")])
        mensagem = erro["msg"].replace("Value error, ", "").replace("Input should be", "O valor deve ser")
        erros_formatados.append(f"Campo '{campo}': {mensagem}")

    return JSONResponse(
        status_code=400,
        content={
            "detail": "Erro de validação nos dados enviados.",
            "errors": erros_formatados,
        },
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

# Frontend (shell de login — autenticação real fica para feature/auth-users)
if FRONTEND_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(FRONTEND_DIR / "static")),
        name="static",
    )

    templates = Jinja2Templates(directory=str(FRONTEND_DIR / "templates"))

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


@app.get("/", tags=["Healthcheck"])
def healthcheck():
    return {
        "status": "ok",
        "message": "WarehouseFlow API operando normalmente!",
    }


@app.get("/health", tags=["Healthcheck"])
def health() -> dict[str, str]:
    return {"status": "ok"}