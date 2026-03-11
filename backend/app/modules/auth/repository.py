"""Queries a la base de datos — Auth, Usuarios, Licencias, Permisos."""
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.auth.models import LicenseType, PermissionObject, UserCompanyLicense, UserPermission
from app.modules.tenants.models import Company, TenantUser


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> TenantUser | None:
        return self.db.query(TenantUser).filter(
            TenantUser.id == user_id,
            TenantUser.deleted_at == None,  # noqa: E711
        ).first()

    def get_by_email(self, email: str) -> TenantUser | None:
        return self.db.query(TenantUser).filter(TenantUser.email == email).first()

    def get_all_by_tenant(self, tenant_id: uuid.UUID) -> list[TenantUser]:
        return self.db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.deleted_at == None,  # noqa: E711
        ).all()

    def create(self, user: TenantUser) -> TenantUser:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: TenantUser) -> TenantUser:
        self.db.commit()
        self.db.refresh(user)
        return user

    def soft_delete(self, user: TenantUser) -> TenantUser:
        from datetime import datetime, timezone
        user.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return user


class LicenseRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_license_type_by_code(self, code: str) -> LicenseType | None:
        return self.db.query(LicenseType).filter(LicenseType.code == code).first()

    def get_all_license_types(self) -> list[LicenseType]:
        return self.db.query(LicenseType).filter(LicenseType.is_active == True).all()  # noqa: E712

    def get_companies_with_licenses(self, user_id: uuid.UUID) -> list[Company]:
        """Retorna las compañías donde el usuario tiene al menos una licencia activa."""
        company_ids = (
            self.db.query(UserCompanyLicense.company_id)
            .filter(
                UserCompanyLicense.user_id == user_id,
                UserCompanyLicense.is_active == True,  # noqa: E712
            )
            .distinct()
            .subquery()
        )
        return (
            self.db.query(Company)
            .filter(
                Company.id.in_(company_ids),
                Company.is_active == True,  # noqa: E712
                Company.deleted_at == None,  # noqa: E711
            )
            .order_by(Company.name)
            .all()
        )

    def get_user_licenses_in_company(
        self, user_id: uuid.UUID, company_id: uuid.UUID
    ) -> list[UserCompanyLicense]:
        return self.db.query(UserCompanyLicense).filter(
            UserCompanyLicense.user_id == user_id,
            UserCompanyLicense.company_id == company_id,
            UserCompanyLicense.is_active == True,  # noqa: E712
        ).all()

    def count_active_licenses_by_type(
        self, tenant_id: uuid.UUID, license_type_id: uuid.UUID
    ) -> int:
        """Cuenta licencias en uso de un tipo específico para el tenant."""
        return (
            self.db.query(func.count(UserCompanyLicense.id))
            .join(TenantUser, TenantUser.id == UserCompanyLicense.user_id)
            .filter(
                TenantUser.tenant_id == tenant_id,
                UserCompanyLicense.license_type_id == license_type_id,
                UserCompanyLicense.is_active == True,  # noqa: E712
            )
            .scalar()
        )

    def get_assignment(
        self, user_id: uuid.UUID, company_id: uuid.UUID, license_type_id: uuid.UUID
    ) -> UserCompanyLicense | None:
        return self.db.query(UserCompanyLicense).filter(
            UserCompanyLicense.user_id == user_id,
            UserCompanyLicense.company_id == company_id,
            UserCompanyLicense.license_type_id == license_type_id,
        ).first()

    def create_assignment(self, assignment: UserCompanyLicense) -> UserCompanyLicense:
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def revoke_assignment(self, assignment: UserCompanyLicense) -> None:
        assignment.is_active = False
        self.db.commit()


class PermissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_object_by_code(self, code: str) -> PermissionObject | None:
        return self.db.query(PermissionObject).filter(PermissionObject.code == code).first()

    def get_all_objects(self, module: str | None = None) -> list[PermissionObject]:
        q = self.db.query(PermissionObject).filter(PermissionObject.is_active == True)  # noqa: E712
        if module:
            q = q.filter(PermissionObject.module == module)
        return q.all()

    def get_user_permission(
        self, user_id: uuid.UUID, company_id: uuid.UUID, object_id: uuid.UUID
    ) -> UserPermission | None:
        return self.db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.company_id == company_id,
            UserPermission.permission_object_id == object_id,
        ).first()

    def get_user_permissions_in_company(
        self, user_id: uuid.UUID, company_id: uuid.UUID
    ) -> list[UserPermission]:
        return self.db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.company_id == company_id,
        ).all()

    def upsert_permission(
        self, user_id: uuid.UUID, company_id: uuid.UUID,
        object_id: uuid.UUID, level: int, set_by: uuid.UUID
    ) -> UserPermission:
        perm = self.get_user_permission(user_id, company_id, object_id)
        if perm:
            perm.level = level
            perm.set_by = set_by
        else:
            perm = UserPermission(
                user_id=user_id,
                company_id=company_id,
                permission_object_id=object_id,
                level=level,
                set_by=set_by,
            )
            self.db.add(perm)
        self.db.commit()
        self.db.refresh(perm)
        return perm
