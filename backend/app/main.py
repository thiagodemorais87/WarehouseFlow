from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import models
from .database import engine, Base, get_db
from .deps import get_current_user_or_none
from .routers import auth, products, tasks, optimization, orders, stock, users, locations
from .routes.optimization import router as optimization_engine_router
from .security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, verify_password

# Inicializa as tabelas no PostgreSQL
Base.metadata.create_all(bind=engine)

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT_DIR / "frontend"

# Página para onde o usuário vai após logar (combinar com a Pessoa 4)
POST_LOGIN_URL = "/inicio"

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

    @app.post("/login", response_class=HTMLResponse, tags=["Frontend"])
    def login_submit(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db),
    ):
        user = db.query(models.User).filter(models.User.email == email).first()

        # Mesma mensagem para e-mail inexistente e senha errada
        if user is None or user.role is None or not verify_password(password, user.password_hash):
            return templates.TemplateResponse(
                "auth/login.html",
                {"request": request, "error": "E-mail ou senha incorretos.", "email": email},
                status_code=401,
            )

        token = create_access_token({"sub": str(user.id), "role": user.role.name})
        response = RedirectResponse(url=POST_LOGIN_URL, status_code=303)
        response.set_cookie(
            "access_token",
            token,
            httponly=True,   # o JavaScript da página não consegue ler o cookie
            samesite="lax",  # não é enviado em requisições vindas de outros sites
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
        role = user.role.name if user.role else None
        return templates.TemplateResponse(
            "inicio.html", {"request": request, "user": user, "role": role}
        )

    @app.post("/logout", tags=["Frontend"])
    def logout():
        response = RedirectResponse(url="/login", status_code=303)
        response.delete_cookie("access_token")
        return response


@app.get("/", tags=["Healthcheck"])
def healthcheck():
    return {"status": "ok", "message": "WarehouseFlow API operando normalmente!"}


@app.get("/health", tags=["Healthcheck"])
def health() -> dict[str, str]:
    return {"status": "ok"}