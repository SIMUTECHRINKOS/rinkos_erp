"""
Lógica de negocio — Tenants y Companies.

Reglas de negocio implementadas aquí:
- Un tenant no puede tener más empresas que las permitidas por su plan.
- El code de tenant y company es único en todo el sistema.
- El schema_name de una company se genera como rinkos_{company_code.lower()}.
- Las configuraciones de moneda e inventario de una company no son modificables
  una vez que settings_locked = True (se sella al postear el primer asiento contable).
"""
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.modules.tenants.models import Company, Tenant
from app.modules.tenants.repository import (
    CompanyRepository,
    SubscriptionPlanRepository,
    TenantRepository,
)
from app.modules.tenants.schemas import CompanyCreate, CompanyUpdate, TenantCreate, TenantUpdate

# UUID del sistema para operaciones sin usuario autenticado (seeds, etc.)
SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class SubscriptionPlanService:
    def __init__(self, db: Session):
        self.repo = SubscriptionPlanRepository(db)

    def listar_planes(self):
        return self.repo.get_all()

    def obtener_plan(self, plan_id: uuid.UUID):
        plan = self.repo.get_by_id(plan_id)
        if not plan:
            raise NotFoundError(f"Plan de suscripción '{plan_id}' no encontrado.")
        return plan


class TenantService:
    def __init__(self, db: Session):
        self.repo = TenantRepository(db)
        self.plan_repo = SubscriptionPlanRepository(db)

    def listar_tenants(self, skip: int = 0, limit: int = 50) -> list[Tenant]:
        return self.repo.get_all(skip=skip, limit=limit)

    def obtener_tenant(self, tenant_id: uuid.UUID) -> Tenant:
        tenant = self.repo.get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError(f"Tenant '{tenant_id}' no encontrado.")
        return tenant

    def crear_tenant(self, data: TenantCreate, created_by: uuid.UUID = SYSTEM_USER_ID) -> Tenant:
        """Crea un nuevo tenant. Valida unicidad de code y email."""
        if self.repo.get_by_code(data.code):
            raise ConflictError(f"Ya existe un tenant con el código '{data.code}'.")
        if self.repo.get_by_email(data.email):
            raise ConflictError(f"Ya existe un tenant con el email '{data.email}'.")

        plan = self.plan_repo.get_by_id(data.plan_id)
        if not plan or not plan.is_active:
            raise NotFoundError(f"Plan de suscripción '{data.plan_id}' no encontrado o inactivo.")

        tenant = Tenant(
            code=data.code,
            name=data.name,
            email=data.email,
            phone=data.phone,
            plan_id=data.plan_id,
            created_by=created_by,
        )
        return self.repo.create(tenant)

    def actualizar_tenant(self, tenant_id: uuid.UUID, data: TenantUpdate) -> Tenant:
        tenant = self.obtener_tenant(tenant_id)

        if data.email and data.email != tenant.email:
            if self.repo.get_by_email(data.email):
                raise ConflictError(f"Ya existe un tenant con el email '{data.email}'.")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(tenant, field, value)

        return self.repo.update(tenant)

    def eliminar_tenant(self, tenant_id: uuid.UUID) -> None:
        tenant = self.obtener_tenant(tenant_id)
        self.repo.soft_delete(tenant)


class CompanyService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CompanyRepository(db)
        self.tenant_repo = TenantRepository(db)
        self.plan_repo = SubscriptionPlanRepository(db)

    def listar_companies(self, tenant_id: uuid.UUID) -> list[Company]:
        self.tenant_repo.get_by_id(tenant_id) or (_ for _ in ()).throw(
            NotFoundError(f"Tenant '{tenant_id}' no encontrado.")
        )
        return self.repo.get_all_by_tenant(tenant_id)

    def obtener_company(self, company_id: uuid.UUID) -> Company:
        company = self.repo.get_by_id(company_id)
        if not company:
            raise NotFoundError(f"Company '{company_id}' no encontrada.")
        return company

    def crear_company(
        self, tenant_id: uuid.UUID, data: CompanyCreate, created_by: uuid.UUID = SYSTEM_USER_ID
    ) -> Company:
        """
        Crea una nueva empresa dentro de un tenant.
        Valida límite de empresas según plan de suscripción.
        Crea el schema PostgreSQL aislado para la empresa.
        """
        tenant = self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError(f"Tenant '{tenant_id}' no encontrado.")

        plan = self.plan_repo.get_by_id(tenant.plan_id)
        empresas_actuales = self.tenant_repo.count_companies(tenant_id)
        if empresas_actuales >= plan.max_companies:
            raise BusinessRuleError(
                f"El plan '{plan.name}' permite máximo {plan.max_companies} empresa(s). "
                f"El tenant ya tiene {empresas_actuales}."
            )

        if self.repo.get_by_code(data.code):
            raise ConflictError(f"Ya existe una empresa con el código '{data.code}'.")

        schema_name = f"rinkos_{data.code.lower()}"

        company = Company(
            tenant_id=tenant_id,
            code=data.code,
            name=data.name,
            legal_name=data.legal_name,
            tax_id=data.tax_id,
            country=data.country,
            currency_lc=data.currency_lc,
            currency_sy=data.currency_sy,
            inventory_method=data.inventory_method,
            schema_name=schema_name,
            created_by=created_by,
        )
        company = self.repo.create(company)

        # Crear el schema PostgreSQL aislado para esta empresa
        self.db.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        self.db.commit()

        return company

    def actualizar_company(self, company_id: uuid.UUID, data: CompanyUpdate) -> Company:
        """
        Actualiza datos de una empresa.
        Los campos currency_lc, currency_sy e inventory_method NO son modificables
        si settings_locked = True (primer asiento contable ya posteado).
        """
        company = self.obtener_company(company_id)

        campos_bloqueados = {"currency_lc", "currency_sy", "inventory_method"}
        if company.settings_locked:
            for campo in campos_bloqueados:
                if getattr(data, campo, None) is not None:
                    raise BusinessRuleError(
                        f"No se puede modificar '{campo}': la empresa ya tiene movimientos contables. "
                        "Bloqueo técnico irreversible."
                    )

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(company, field, value)

        return self.repo.update(company)

    def eliminar_company(self, company_id: uuid.UUID) -> None:
        company = self.obtener_company(company_id)
        self.repo.soft_delete(company)
