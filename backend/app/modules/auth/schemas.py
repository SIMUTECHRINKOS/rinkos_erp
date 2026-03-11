"""Schemas Pydantic — Auth, Usuarios y Licencias."""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ─── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    company_id: uuid.UUID


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    full_name: str
    is_superuser: bool
    company_id: uuid.UUID
    modules: list[str]  # módulos accesibles según licencias en esta compañía


# ─── Usuarios ─────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=200)
    password: str = Field(..., min_length=8)
    is_superuser: bool = False


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=200)
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Licencias ────────────────────────────────────────────────────────────────

class LicenseTypeResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    modules_allowed: list[str]

    model_config = {"from_attributes": True}


class AssignLicenseRequest(BaseModel):
    user_id: uuid.UUID
    company_id: uuid.UUID
    license_type_code: str


class RevokeLicenseRequest(BaseModel):
    user_id: uuid.UUID
    company_id: uuid.UUID
    license_type_code: str


class TenantLicenseSummary(BaseModel):
    """Resumen de uso de licencias del tenant."""
    license_type: str
    quota: int
    used: int
    available: int


# ─── Permisos ─────────────────────────────────────────────────────────────────

class PermissionObjectResponse(BaseModel):
    id: uuid.UUID
    module: str
    code: str
    name: str

    model_config = {"from_attributes": True}


class SetPermissionRequest(BaseModel):
    user_id: uuid.UUID
    company_id: uuid.UUID
    permission_object_code: str
    level: int = Field(..., ge=0, le=2)  # 0=NINGUNO, 1=LECTURA, 2=TOTAL


class UserPermissionResponse(BaseModel):
    permission_object_code: str
    permission_object_name: str
    module: str
    level: int
    level_label: str  # "NINGUNO" | "LECTURA" | "TOTAL"

    model_config = {"from_attributes": True}
