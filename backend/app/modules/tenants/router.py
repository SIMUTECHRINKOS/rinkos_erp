"""
Endpoints FastAPI — Tenants y Companies.

Prefijo: /api/v1/tenants
"""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError, business_rule_error, conflict, not_found
from app.modules.tenants.schemas import (
    CompanyCreate,
    CompanyResponse,
    CompanyUpdate,
    SubscriptionPlanResponse,
    TenantCreate,
    TenantResponse,
    TenantUpdate,
)
from app.modules.tenants.service import CompanyService, SubscriptionPlanService, TenantService

router = APIRouter(prefix="/tenants", tags=["Tenants"])


# ─── Planes de Suscripción ────────────────────────────────────────────────────

@router.get("/planes", response_model=list[SubscriptionPlanResponse])
def listar_planes(db: Session = Depends(get_db)):
    """Lista todos los planes de suscripción activos."""
    return SubscriptionPlanService(db).listar_planes()


@router.get("/planes/{plan_id}", response_model=SubscriptionPlanResponse)
def obtener_plan(plan_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return SubscriptionPlanService(db).obtener_plan(plan_id)
    except NotFoundError as e:
        raise not_found("Plan", str(plan_id))


# ─── Tenants ──────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[TenantResponse])
def listar_tenants(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Lista todos los tenants activos."""
    return TenantService(db).listar_tenants(skip=skip, limit=limit)


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def crear_tenant(data: TenantCreate, db: Session = Depends(get_db)):
    try:
        return TenantService(db).crear_tenant(data)
    except NotFoundError:
        raise not_found("Plan", str(data.plan_id))
    except ConflictError as e:
        raise conflict(str(e))


@router.get("/{tenant_id}", response_model=TenantResponse)
def obtener_tenant(tenant_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return TenantService(db).obtener_tenant(tenant_id)
    except NotFoundError:
        raise not_found("Tenant", str(tenant_id))


@router.patch("/{tenant_id}", response_model=TenantResponse)
def actualizar_tenant(tenant_id: uuid.UUID, data: TenantUpdate, db: Session = Depends(get_db)):
    try:
        return TenantService(db).actualizar_tenant(tenant_id, data)
    except NotFoundError:
        raise not_found("Tenant", str(tenant_id))
    except ConflictError as e:
        raise conflict(str(e))


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tenant(tenant_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        TenantService(db).eliminar_tenant(tenant_id)
    except NotFoundError:
        raise not_found("Tenant", str(tenant_id))


# ─── Companies ────────────────────────────────────────────────────────────────

@router.get("/{tenant_id}/companies", response_model=list[CompanyResponse])
def listar_companies(tenant_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return CompanyService(db).listar_companies(tenant_id)
    except NotFoundError:
        raise not_found("Tenant", str(tenant_id))


@router.post(
    "/{tenant_id}/companies",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_company(tenant_id: uuid.UUID, data: CompanyCreate, db: Session = Depends(get_db)):
    try:
        return CompanyService(db).crear_company(tenant_id, data)
    except NotFoundError as e:
        raise not_found("Tenant", str(tenant_id))
    except ConflictError as e:
        raise conflict(str(e))
    except BusinessRuleError as e:
        raise business_rule_error(str(e))


@router.get("/{tenant_id}/companies/{company_id}", response_model=CompanyResponse)
def obtener_company(tenant_id: uuid.UUID, company_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return CompanyService(db).obtener_company(company_id)
    except NotFoundError:
        raise not_found("Company", str(company_id))


@router.patch("/{tenant_id}/companies/{company_id}", response_model=CompanyResponse)
def actualizar_company(
    tenant_id: uuid.UUID, company_id: uuid.UUID, data: CompanyUpdate, db: Session = Depends(get_db)
):
    try:
        return CompanyService(db).actualizar_company(company_id, data)
    except NotFoundError:
        raise not_found("Company", str(company_id))
    except BusinessRuleError as e:
        raise business_rule_error(str(e))


@router.delete("/{tenant_id}/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_company(
    tenant_id: uuid.UUID, company_id: uuid.UUID, db: Session = Depends(get_db)
):
    try:
        CompanyService(db).eliminar_company(company_id)
    except NotFoundError:
        raise not_found("Company", str(company_id))
