"""Smoke de integração auth + CRUD (SQLite em memória via conftest)."""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Role, User
from app.security import hash_password


def _seed_admin() -> None:
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        if not db.query(Role).filter(Role.name == "ADMIN").first():
            db.add(Role(id=1, name="ADMIN"))
            db.commit()
        if not db.query(User).filter(User.email == "admin@test.com").first():
            db.add(
                User(
                    name="Admin Test",
                    email="admin@test.com",
                    password_hash=hash_password("admin123"),
                    role_id=1,
                    is_active=True,
                )
            )
            db.commit()
    finally:
        db.close()


_seed_admin()
client = TestClient(app)


def test_login_and_products_require_auth():
    denied = client.get("/products/")
    assert denied.status_code == 401

    login = client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "admin123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    ok = client.get(
        "/products/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ok.status_code == 200
