"""
Modelos SQLAlchemy — Fase 1A/1B: Tenants, Companies, Planes de Suscripción.

Jerarquía:
  SubscriptionPlan → Tenant (1..N companies) → Company (schema propio)

Todas las tablas viven en el schema 'public'.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.base_model import TimestampMixin


class SubscriptionPlan(Base):
    """
    Planes de suscripción disponibles en RINKOS ERP.
    Datos semilla: Basic / Pro / Enterprise.
    Incluye cuota de licencias por tipo confirmada.

    | Plan       | prof | log | fin | crm |
    |------------|------|-----|-----|-----|
    | Basic      |  1   |  0  |  1  |  1  |
    | Pro        |  1   |  2  |  1  |  2  |
    | Enterprise |  3   |  5  |  2  |  5  |
    """
    __tablename__ = "subscription_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_companies: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_users: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    # Cuota de licencias por tipo
    quota_professional: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quota_logistics: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quota_finance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quota_crm: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    tenants: Mapped[list["Tenant"]] = relationship("Tenant", back_populates="plan")


class Tenant(Base, TimestampMixin):
    """
    Organización cliente de RINKOS ERP.
    Un tenant puede tener múltiples empresas (companies).
    """
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    plan: Mapped["SubscriptionPlan"] = relationship("SubscriptionPlan", back_populates="tenants")
    companies: Mapped[list["Company"]] = relationship("Company", back_populates="tenant")
    users: Mapped[list["TenantUser"]] = relationship("TenantUser", back_populates="tenant")


class Company(Base, TimestampMixin):
    """
    Empresa dentro de un tenant.
    Cada company tiene su propio schema PostgreSQL: rinkos_{company_code}.
    Las configuraciones de moneda y valorización se sellan al postear el primer asiento.
    """
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    country: Mapped[str] = mapped_column(String(3), nullable=False, default="DOM")
    currency_lc: Mapped[str] = mapped_column(String(3), nullable=False)
    currency_sy: Mapped[str] = mapped_column(String(3), nullable=False)
    inventory_method: Mapped[str] = mapped_column(
        String(10), nullable=False, default="AVG"
    )  # AVG=Promedio Ponderado, FIFO=FIFO
    schema_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Bloqueo técnico: True una vez que se postea el primer asiento contable
    settings_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="companies")
    user_access: Mapped[list["UserCompanyAccess"]] = relationship(
        "UserCompanyAccess", back_populates="company"
    )


class TenantUser(Base, TimestampMixin):
    """
    Usuario del sistema. Pertenece a un tenant.
    Acceso a empresas específicas vía UserCompanyAccess y UserCompanyLicense.

    is_superuser: solo aplica si el usuario tiene licencia PROFESSIONAL.
    Con is_superuser=True puede gestionar licencias y configurar permisos.
    """
    __tablename__ = "tenant_users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    company_access: Mapped[list["UserCompanyAccess"]] = relationship(
        "UserCompanyAccess", back_populates="user"
    )


class UserCompanyAccess(Base):
    """Qué empresas puede usar cada usuario dentro del tenant."""
    __tablename__ = "user_company_access"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenant_users.id"), nullable=False
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["TenantUser"] = relationship("TenantUser", back_populates="company_access")
    company: Mapped["Company"] = relationship("Company", back_populates="user_access")


class AuditLog(Base):
    """
    Registro de auditoría global del sistema.
    Inmutable: nunca se actualiza ni se borra.
    """
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    entity: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
