"""Queries a la base de datos — sin lógica de negocio."""
import uuid

from sqlalchemy.orm import Session

from app.modules.tenants.models import Company, SubscriptionPlan, Tenant


class SubscriptionPlanRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[SubscriptionPlan]:
        return self.db.query(SubscriptionPlan).filter(
            SubscriptionPlan.is_active == True  # noqa: E712
        ).all()

    def get_by_id(self, plan_id: uuid.UUID) -> SubscriptionPlan | None:
        return self.db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == plan_id
        ).first()


class TenantRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 50) -> list[Tenant]:
        return self.db.query(Tenant).filter(
            Tenant.deleted_at == None  # noqa: E711
        ).offset(skip).limit(limit).all()

    def get_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        return self.db.query(Tenant).filter(
            Tenant.id == tenant_id,
            Tenant.deleted_at == None,  # noqa: E711
        ).first()

    def get_by_code(self, code: str) -> Tenant | None:
        return self.db.query(Tenant).filter(Tenant.code == code).first()

    def get_by_email(self, email: str) -> Tenant | None:
        return self.db.query(Tenant).filter(Tenant.email == email).first()

    def create(self, tenant: Tenant) -> Tenant:
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def update(self, tenant: Tenant) -> Tenant:
        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def soft_delete(self, tenant: Tenant) -> Tenant:
        from datetime import datetime, timezone
        tenant.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return tenant

    def count_companies(self, tenant_id: uuid.UUID) -> int:
        return self.db.query(Company).filter(
            Company.tenant_id == tenant_id,
            Company.deleted_at == None,  # noqa: E711
        ).count()


class CompanyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_by_tenant(self, tenant_id: uuid.UUID) -> list[Company]:
        return self.db.query(Company).filter(
            Company.tenant_id == tenant_id,
            Company.deleted_at == None,  # noqa: E711
        ).all()

    def get_by_id(self, company_id: uuid.UUID) -> Company | None:
        return self.db.query(Company).filter(
            Company.id == company_id,
            Company.deleted_at == None,  # noqa: E711
        ).first()

    def get_by_code(self, code: str) -> Company | None:
        return self.db.query(Company).filter(Company.code == code).first()

    def create(self, company: Company) -> Company:
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return company

    def update(self, company: Company) -> Company:
        self.db.commit()
        self.db.refresh(company)
        return company

    def soft_delete(self, company: Company) -> Company:
        from datetime import datetime, timezone
        company.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return company
