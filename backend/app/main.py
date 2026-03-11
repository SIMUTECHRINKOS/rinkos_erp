from fastapi import FastAPI

from app.core.config import settings
from app.modules.tenants.router import router as tenants_router

app = FastAPI(
    title="RINKOS ERP API",
    version="0.1.0",
    description="API REST de RINKOS ERP — Fase 1A: Multi-Tenant + Companies",
)

app.include_router(tenants_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}
