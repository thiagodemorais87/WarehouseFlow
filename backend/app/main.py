from __future__ import annotations

from fastapi import FastAPI

from app.routes.optimization import router as optimization_router

app = FastAPI(
    title="WarehouseFlow",
    description="API do WarehouseFlow — motor de otimização de picking",
    version="0.1.0",
)

app.include_router(optimization_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
