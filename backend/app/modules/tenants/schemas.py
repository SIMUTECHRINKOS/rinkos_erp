"""Schemas Pydantic para Tenants, Companies y Planes de Suscripción."""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# ─── Subscription Plan ────────────────────────────────────────────────────────

class SubscriptionPlanResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: str | None
    max_companies: int
    max_users: int
    is_active: bool

    model_config = {"from_attributes": True}


# ─── Tenant ───────────────────────────────────────────────────────────────────

class TenantCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=20, pattern=r"^[A-Z0-9_]+$")
    name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    phone: str | None = None
    plan_id: uuid.UUID


class TenantUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    email: EmailStr | None = None
    phone: str | None = None
    plan_id: uuid.UUID | None = None
    is_active: bool | None = None


class TenantResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    email: str
    phone: str | None
    plan_id: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Company ──────────────────────────────────────────────────────────────────

class CompanyCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=20, pattern=r"^[A-Z0-9_]+$")
    name: str = Field(..., min_length=2, max_length=200)
    legal_name: str | None = None
    tax_id: str | None = None
    country: str = Field(default="DOM", min_length=2, max_length=3)
    currency_lc: str = Field(..., min_length=3, max_length=3)
    currency_sy: str = Field(..., min_length=3, max_length=3)
    inventory_method: Literal["AVG", "FIFO"] = "AVG"


class CompanyUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    legal_name: str | None = None
    tax_id: str | None = None
    is_active: bool | None = None
    # Campos bloqueados tras el primer asiento contable (settings_locked = True)
    currency_lc: str | None = Field(None, min_length=3, max_length=3)
    currency_sy: str | None = Field(None, min_length=3, max_length=3)
    inventory_method: Literal["AVG", "FIFO"] | None = None


class CompanyResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    code: str
    name: str
    legal_name: str | None
    tax_id: str | None
    country: str
    currency_lc: str
    currency_sy: str
    inventory_method: str
    schema_name: str
    is_active: bool
    settings_locked: bool
    created_at: datetime

    model_config = {"from_attributes": True}
