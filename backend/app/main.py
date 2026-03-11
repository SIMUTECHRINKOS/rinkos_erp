from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.seeds import run_seeds
from app.modules.auth.router import router as auth_router
from app.modules.tenants.router import router as tenants_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        run_seeds(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="RINKOS ERP API",
    version="0.2.0",
    description="API REST de RINKOS ERP — Fase 1B: Auth + Usuarios + Licencias",
    lifespan=lifespan,
)

app.include_router(tenants_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.2.0"}
