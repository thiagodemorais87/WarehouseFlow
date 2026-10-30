from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Form, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import models
from .database import Base, engine, get_db
from .deps import get_current_user_or_none
from .routers import (
    auth,
    locations,
    optimization,
    orders,
    products,
    reports, 
    stock,
    tasks,
    users,
)
from .routers.optimization_engine import router as optimization_engine_router
from .security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, verify_password

# Inicializa as tabelas no PostgreSQL
Base.metadata.create_all(bind=engine)

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", str(ROOT_DIR / "frontend"))).resolve()
APP_VERSION = os.getenv("APP_VERSION", "dev")

# Página para onde o usuário vai após logar via formulário (cookie)
POST_LOGIN_URL = "/inicio"

app = FastAPI(
    title="WarehouseFlow API",
    description="API inteligente para gerenciamento e otimização de operações em armazéns.",
    version=APP_VERSION,
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
app.include_router(reports.router)  

# Motor de otimização de picking
app.include_router(optimization_engine_router)

# Frontend Jinja (login, dashboard, produtos, estoque, posições)
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

    @app.post("/login", response_class=HTMLResponse, tags=["Frontend"])
    def login_submit(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db),
    ):
        user = db.query(models.User).filter(models.User.email == email).first()

        if (
            user is None
            or user.role is None
            or not verify_password(password, user.password_hash)
            or not getattr(user, "is_active", True)
        ):
            return templates.TemplateResponse(
                request=request,
                name="auth/login.html",
                context={"error": "E-mail ou senha incorretos.", "email": email},
                status_code=401,
            )

        role_name = user.role_name or (user.role.name if user.role else "OPERADOR")
        token = create_access_token(
            {"sub": str(user.id), "email": user.email, "role": role_name}
        )
        response = RedirectResponse(url=POST_LOGIN_URL, status_code=303)
        response.set_cookie(
            "access_token",
            token,
            httponly=True,
            samesite="lax",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        return response

    @app.get("/inicio", response_class=HTMLResponse, tags=["Frontend"])
    def inicio_page(
        request: Request,
        user: Optional[models.User] = Depends(get_current_user_or_none),
    ):
        if user is None:
            return RedirectResponse(url="/login", status_code=303)
        role = user.role_name or (user.role.name if user.role else None)
        return templates.TemplateResponse(
            request=request,
            name="inicio.html",
            context={"user": user, "role": role},
        )

    @app.post("/logout", tags=["Frontend"])
    def logout():
        response = RedirectResponse(url="/login", status_code=303)
        response.delete_cookie("access_token")
        return response

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

    @app.get(
        "/pedidos",
        response_class=HTMLResponse,
        tags=["Frontend"],
    )
    def orders_page(request: Request):
        user = {
            "name": "Usuário Teste",
            "initials": "UT",
            "role": "Administrador",
        }

        return templates.TemplateResponse(
            request=request,
            name="orders/orders.html",
            context={
                "user": user,
                "active_page": "orders",
            },
        )

    @app.get("/tarefas", response_class=HTMLResponse, tags=["Frontend"])
    def tasks_page(request: Request):
        user = {
            "name": "Usuário Teste",
            "initials": "UT",
            "role": "Administrador",
        }

        return templates.TemplateResponse(
            request=request,
            name="tasks/tasks.html",
            context={
                "user": user,
                "active_page": "tasks",
            },
        )

    @app.get(
        "/otimizacao",
        response_class=HTMLResponse,
        tags=["Frontend"],
    )
    def optimization_page(request: Request):
        user = {
            "name": "Usuário Teste",
            "initials": "UT",
            "role": "Administrador",
        }

        return templates.TemplateResponse(
            request=request,
            name="optimization/optimization.html",
            context={
                "user": user,
                "active_page": "optimization",
            },
        )

    @app.get(
        "/relatorios/picking",
        response_class=HTMLResponse,
        tags=["Frontend"],
    )
    def picking_report_page(request: Request):
        user = {
            "name": "Usuário Teste",
            "initials": "UT",
            "role": "Administrador",
        }

        return templates.TemplateResponse(
            request=request,
            name="reports/picking.html",
            context={
                "user": user,
                "active_page": "picking_report",
            },
        )

    @app.get(
        "/relatorios/movimentacoes",
        response_class=HTMLResponse,
        tags=["Frontend"]
    )
    def stock_movements_report_page(request: Request):
        user = {
            "name": "Usuário Teste",
            "initials": "UT",
            "role": "Administrador"
        }

        return templates.TemplateResponse(
            request=request,
            name="reports/stock-movements.html",
            context={
                "user": user,
                "active_page": "stock_movements_report"
            }
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
    return {"status": "ok", "version": APP_VERSION}
