from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Form, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
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
from .security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_HTTPONLY,
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    create_access_token,
    verify_password,
)

# Inicializa as tabelas no PostgreSQL
Base.metadata.create_all(bind=engine)

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", str(ROOT_DIR / "frontend"))).resolve()
APP_VERSION = os.getenv("APP_VERSION", "dev")
ENABLE_DOCS = os.getenv("ENABLE_DOCS", "true").lower() in ("1", "true", "yes")

# Página para onde o usuário vai após logar via formulário (cookie)
POST_LOGIN_URL = "/inicio"

app = FastAPI(
    title="WarehouseFlow API",
    description="API inteligente para gerenciamento e otimização de operações em armazéns.",
    version=APP_VERSION,
    docs_url="/docs" if ENABLE_DOCS else None,
    redoc_url="/redoc" if ENABLE_DOCS else None,
    openapi_url="/openapi.json" if ENABLE_DOCS else None,
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


def _integrity_response(exc: IntegrityError) -> tuple[int, str]:
    """Classifica a violação: duplicidade/vínculo = 409; NOT NULL/CHECK = 400."""
    orig = getattr(exc, "orig", None)
    pgcode = getattr(orig, "pgcode", None)
    texto = str(orig).lower()
    if pgcode == "23505" or "unique" in texto or "duplicate key" in texto:
        return 409, "Registro duplicado: já existe um registro com estes dados."
    if pgcode == "23503" or "foreign key" in texto:
        return 409, "Operação bloqueada: o registro possui vínculos ou referencia um registro inexistente."
    return 400, "Os dados enviados violam uma regra de integridade do banco."


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    status_code, detail = _integrity_response(exc)
    logger.warning("IntegrityError em %s %s: %s", request.method, request.url.path, exc.orig)
    return JSONResponse(status_code=status_code, content={"detail": detail})


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
            httponly=COOKIE_HTTPONLY,
            samesite=COOKIE_SAMESITE,
            secure=COOKIE_SECURE,
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
        response.delete_cookie(
            "access_token",
            httponly=COOKIE_HTTPONLY,
            samesite=COOKIE_SAMESITE,
            secure=COOKIE_SECURE,
        )
        return response

    def _user_context(user: models.User) -> dict:
        """Dados do usuário logado para o topo e o menu das páginas."""
        partes = (user.name or "").split()
        iniciais = "".join(p[0] for p in partes[:2]).upper() or "U"
        return {"name": user.name, "initials": iniciais, "role": user.role_name or ""}

    def _register_page(path: str, template: str, active_page: str) -> None:
        @app.get(
            path,
            response_class=HTMLResponse,
            tags=["Frontend"],
            include_in_schema=False,
        )
        def page(
            request: Request,
            user: Optional[models.User] = Depends(get_current_user_or_none),
        ):
            # Usuários não autenticados devem retornar ao login.
            if user is None:
                return RedirectResponse(url="/login", status_code=303)

            # Relatório de movimentações: exclusivo para ADMIN e GESTOR.
            if path == "/relatorios/movimentacoes":
                role = (user.role_name or "").strip().upper()

                # Compatibilidade com perfis antigos do banco.
                if role == "MANAGER":
                    role = "GESTOR"

                if role not in ("ADMIN", "GESTOR"):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=(
                            "Acesso negado: seu perfil não possui permissão "
                            "para visualizar este relatório."
                        ),
                    )

            # Gerenciamento de usuários: exclusivo para ADMIN.
            if path == "/usuarios":
                role = (
                    user.role_name
                    or (user.role.name if user.role else "")
                ).strip().upper()

                if role != "ADMIN":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=(
                            "Acesso negado: somente administradores "
                            "podem gerenciar usuários."
                        ),
                    )

            return templates.TemplateResponse(
                request=request,
                name=template,
                context={
                    "user": _user_context(user),
                    "active_page": active_page,
                },
            )

    for _path, _template, _active in [
        ("/dashboard", "dashboard/dashboard.html", "dashboard"),
        ("/produtos", "products/products.html", "products"),
        ("/estoque", "inventory/stock.html", "stock"),
        ("/posicoes", "locations/locations.html", "locations"),
        ("/pedidos", "orders/orders.html", "orders"),
        ("/tarefas", "tasks/tasks.html", "tasks"),
        ("/relatorios/picking", "reports/picking.html", "picking_report"),
        ("/relatorios/movimentacoes", "reports/stock-movements.html", "stock_movements_report"),
        ("/usuarios", "users/users.html", "users"),
    ]:
        _register_page(_path, _template, _active)

    def _parse_order_ids(raw: str) -> list[int]:
        parts = [p.strip() for p in raw.replace(";", ",").replace(" ", ",").split(",")]
        ids: list[int] = []
        for part in parts:
            if not part:
                continue
            ids.append(int(part))
        return ids

    def _render_otimizacao(
        request: Request,
        user: models.User,
        *,
        mode: str = "manual",
        batch_result: dict | None = None,
        batch_error: str | None = None,
        batch_form: dict | None = None,
    ):
        return templates.TemplateResponse(
            request=request,
            name="optimization/optimization.html",
            context={
                "user": _user_context(user),
                "active_page": "optimization",
                "mode": mode if mode in ("manual", "order", "batch") else "manual",
                "batch_result": batch_result,
                "batch_error": batch_error,
                "batch_form": batch_form
                or {"order_ids": "", "workers": "2", "repeats": "4"},
            },
        )

    @app.get(
        "/otimizacao",
        response_class=HTMLResponse,
        tags=["Frontend"],
        include_in_schema=False,
    )
    def otimizacao_page(
        request: Request,
        mode: str = "manual",
        user: Optional[models.User] = Depends(get_current_user_or_none),
    ):
        if user is None:
            return RedirectResponse(url="/login", status_code=303)
        return _render_otimizacao(request, user, mode=mode)

    @app.post(
        "/otimizacao/lote",
        response_class=HTMLResponse,
        tags=["Frontend"],
        include_in_schema=False,
    )
    def otimizacao_lote_submit(
        request: Request,
        order_ids: str = Form(...),
        workers: int = Form(2),
        repeats: int = Form(4),
        user: Optional[models.User] = Depends(get_current_user_or_none),
        db: Session = Depends(get_db),
    ):
        """Lote paralelo 100% server-side (Python/C) — sem JS de cálculo."""
        if user is None:
            return RedirectResponse(url="/login", status_code=303)

        form_state = {
            "order_ids": order_ids,
            "workers": str(workers),
            "repeats": str(repeats),
        }

        try:
            parsed_ids = _parse_order_ids(order_ids)
        except ValueError:
            return _render_otimizacao(
                request,
                user,
                mode="batch",
                batch_error="IDs inválidos. Use números separados por vírgula (ex.: 1, 2, 3).",
                batch_form=form_state,
            )

        if not parsed_ids:
            return _render_otimizacao(
                request,
                user,
                mode="batch",
                batch_error="Informe ao menos um order_id válido.",
                batch_form=form_state,
            )
        if len(set(parsed_ids)) != len(parsed_ids):
            return _render_otimizacao(
                request,
                user,
                mode="batch",
                batch_error="order_ids contém duplicados.",
                batch_form=form_state,
            )

        workers = max(1, min(int(workers), 16))
        repeats = max(1, min(int(repeats), 50))

        from optimization.types import Location

        from .providers.sqlalchemy import SqlAlchemyOrderRouteProvider
        from .routers.optimization_engine import OptimizationRunRecorder
        from .services.optimization_service import (
            is_native_compiled,
            optimize_batch_from_order_ids,
        )

        provider = SqlAlchemyOrderRouteProvider(db)
        recorder = OptimizationRunRecorder(db)
        start = Location(id="START", x=0.0, y=0.0)

        try:
            ids, batch = optimize_batch_from_order_ids(
                parsed_ids,
                provider,
                start=start,
                workers=workers,
                repeats=repeats,
            )
        except KeyError as exc:
            return _render_otimizacao(
                request,
                user,
                mode="batch",
                batch_error=str(exc),
                batch_form=form_state,
            )
        except ValueError as exc:
            return _render_otimizacao(
                request,
                user,
                mode="batch",
                batch_error=str(exc),
                batch_form=form_state,
            )

        rows = []
        for order_id, result in zip(ids, batch.results):
            recorder.save(user, result, source="batch", order_id=order_id)
            rows.append(
                {
                    "order_id": order_id,
                    "distance_before": result.distance_before,
                    "distance_after": result.distance_after,
                    "reduction_percent": result.reduction_percent,
                    "two_opt_route": " → ".join(result.two_opt_route),
                }
            )

        batch_result = {
            "sequential_ms": batch.sequential_ms,
            "parallel_ms": batch.parallel_ms,
            "speedup": batch.speedup,
            "efficiency": batch.efficiency,
            "workers": batch.workers,
            "orders_count": batch.jobs_count,
            "native_compiled": is_native_compiled(),
            "rows": rows,
        }
        return _render_otimizacao(
            request,
            user,
            mode="batch",
            batch_result=batch_result,
            batch_form=form_state,
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


@app.get("/ready", tags=["Healthcheck"])
def ready() -> JSONResponse:
    """Readiness: verifica conectividade real com o PostgreSQL."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return JSONResponse(status_code=200, content={"status": "ready"})
    except Exception:
        logger.exception("Readiness check falhou: banco indisponível")
        return JSONResponse(status_code=503, content={"status": "not_ready"})


def custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    validation_error = {
        "description": "Erro de validação nos dados enviados.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["detail", "errors"],
                    "properties": {
                        "detail": {"type": "string"},
                        "errors": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                }
            }
        },
    }

    for path in schema["paths"].values():
        for operation in path.values():
            responses = operation.get("responses", {})
            if "422" in responses:
                responses.pop("422")
                responses["400"] = validation_error

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi