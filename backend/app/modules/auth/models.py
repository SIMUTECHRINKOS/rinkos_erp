"""
Modelos SQLAlchemy — Fase 1B: Auth, Licencias y Permisos.

Tablas en schema 'public':
  - license_types          → 4 tipos semilla (Professional, Logistics, Finance, CRM)
  - tenant_users           → extendido con hashed_password
  - user_company_licenses  → licencias asignadas por usuario por compañía
  - permission_objects     → catálogo de objetos/funciones configurables
  - user_permissions       → nivel de permiso por usuario por objeto en una compañía
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, SmallInteger, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.base_model import TimestampMixin


class LicenseType(Base):
    """
    Tipos de licencia disponibles en RINKOS ERP.
    Datos semilla: PROFESSIONAL, LOGISTICS, FINANCE, CRM.
    Define qué módulos son accesibles para cada tipo.
    """
    __tablename__ = "license_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Módulos accesibles como lista separada por comas (ej: "accounting,ar,ap")
    modules_allowed: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user_licenses: Mapped[list["UserCompanyLicense"]] = relationship(
        "UserCompanyLicense", back_populates="license_type"
    )


class UserCompanyLicense(Base):
    """
    Licencias asignadas a un usuario en una compañía específica.
    Un usuario puede tener múltiples licencias en la misma compañía.
    Cada asignación consume 1 licencia del cupo del tenant.
    """
    __tablename__ = "user_company_licenses"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", "license_type_id", name="uq_user_company_license"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenant_users.id"), nullable=False
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )
    license_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("license_types.id"), nullable=False
    )
    granted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    license_type: Mapped["LicenseType"] = relationship(
        "LicenseType", back_populates="user_licenses"
    )


class PermissionObject(Base):
    """
    Catálogo de objetos/funciones del sistema que tienen permisos configurables.
    Ej: 'sales_invoice', 'customer_master', 'journal_entry'.
    Se agregan módulo a módulo durante el desarrollo.
    """
    __tablename__ = "permission_objects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user_permissions: Mapped[list["UserPermission"]] = relationship(
        "UserPermission", back_populates="permission_object"
    )


class UserPermission(Base):
    """
    Permiso de un usuario sobre un objeto en una compañía.

    Niveles:
      0 = NINGUNO  → sin acceso
      1 = LECTURA  → solo consultar
      2 = TOTAL    → crear, actualizar y cancelar/anular

    Solo un usuario con licencia PROFESSIONAL + is_superuser=True puede
    crear/modificar estos registros.
    """
    __tablename__ = "user_permissions"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", "permission_object_id", name="uq_user_company_permission"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenant_users.id"), nullable=False
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )
    permission_object_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("permission_objects.id"), nullable=False
    )
    level: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    set_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    permission_object: Mapped["PermissionObject"] = relationship(
        "PermissionObject", back_populates="user_permissions"
    )
