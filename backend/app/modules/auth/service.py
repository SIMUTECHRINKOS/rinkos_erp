"""
Lógica de negocio — Auth, Usuarios, Licencias y Permisos.

Reglas implementadas:
- Solo SuperUsuario Profesional puede asignar/revocar licencias y configurar permisos.
- No se puede exceder la cuota de licencias del tenant.
- Los módulos accesibles son la unión de los módulos de todas las licencias del usuario.
- Los permisos son por usuario por compañía por objeto.
- Un usuario solo puede recibir permisos en módulos a los que su licencia da acceso.
"""
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.models import LicenseType, UserCompanyLicense
from app.modules.auth.repository import LicenseRepository, PermissionRepository, UserRepository
from app.modules.auth.schemas import (
    AssignLicenseRequest,
    LoginRequest,
    SetPermissionRequest,
    TokenResponse,
    UserCreate,
    UserUpdate,
)
from app.modules.tenants.models import TenantUser
from app.modules.tenants.repository import CompanyRepository, TenantRepository

PERMISSION_LABELS = {0: "NINGUNO", 1: "LECTURA", 2: "TOTAL"}
SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.license_repo = LicenseRepository(db)
        self.company_repo = CompanyRepository(db)

    def login(self, data: LoginRequest) -> TokenResponse:
        """Autentica al usuario y devuelve un JWT con sus módulos accesibles."""
        user = self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise BusinessRuleError("Credenciales incorrectas.")
        if not user.is_active:
            raise BusinessRuleError("Usuario inactivo.")

        company = self.company_repo.get_by_id(data.company_id)
        if not company or not company.is_active:
            raise NotFoundError(f"Compañía '{data.company_id}' no encontrada o inactiva.")

        # Verificar que el usuario tiene acceso a esta compañía
        licenses = self.license_repo.get_user_licenses_in_company(user.id, data.company_id)
        if not licenses:
            raise BusinessRuleError("El usuario no tiene licencias asignadas en esta compañía.")

        modules = self._get_modules_from_licenses(licenses)

        token = create_access_token({
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "company_id": str(data.company_id),
            "is_superuser": user.is_superuser,
            "modules": modules,
        })

        return TokenResponse(
            access_token=token,
            user_id=user.id,
            full_name=user.full_name,
            is_superuser=user.is_superuser,
            company_id=data.company_id,
            modules=modules,
        )

    def _get_modules_from_licenses(self, licenses: list[UserCompanyLicense]) -> list[str]:
        """Devuelve la unión de módulos de todas las licencias activas."""
        modules: set[str] = set()
        for lic in licenses:
            if lic.license_type and lic.license_type.modules_allowed:
                for m in lic.license_type.modules_allowed.split(","):
                    modules.add(m.strip())
        return sorted(modules)


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.tenant_repo = TenantRepository(db)

    def listar_usuarios(self, tenant_id: uuid.UUID) -> list[TenantUser]:
        return self.user_repo.get_all_by_tenant(tenant_id)

    def obtener_usuario(self, user_id: uuid.UUID) -> TenantUser:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"Usuario '{user_id}' no encontrado.")
        return user

    def crear_usuario(
        self, tenant_id: uuid.UUID, data: UserCreate, created_by: uuid.UUID = SYSTEM_USER_ID
    ) -> TenantUser:
        if self.user_repo.get_by_email(data.email):
            raise ConflictError(f"Ya existe un usuario con el email '{data.email}'.")

        tenant = self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError(f"Tenant '{tenant_id}' no encontrado.")

        user = TenantUser(
            tenant_id=tenant_id,
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            is_superuser=data.is_superuser,
            created_by=created_by,
        )
        return self.user_repo.create(user)

    def actualizar_usuario(self, user_id: uuid.UUID, data: UserUpdate) -> TenantUser:
        user = self.obtener_usuario(user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        return self.user_repo.update(user)

    def cambiar_password(
        self, user_id: uuid.UUID, current_password: str, new_password: str
    ) -> None:
        user = self.obtener_usuario(user_id)
        if not verify_password(current_password, user.hashed_password):
            raise BusinessRuleError("La contraseña actual es incorrecta.")
        user.hashed_password = hash_password(new_password)
        self.user_repo.update(user)

    def eliminar_usuario(self, user_id: uuid.UUID) -> None:
        user = self.obtener_usuario(user_id)
        self.user_repo.soft_delete(user)


class LicenseService:
    def __init__(self, db: Session):
        self.db = db
        self.license_repo = LicenseRepository(db)
        self.user_repo = UserRepository(db)
        self.tenant_repo = TenantRepository(db)
        self.company_repo = CompanyRepository(db)

    def listar_tipos(self) -> list[LicenseType]:
        return self.license_repo.get_all_license_types()

    def resumen_licencias_tenant(self, tenant_id: uuid.UUID) -> list[dict]:
        """Devuelve uso de licencias del tenant vs. cuota del plan."""
        tenant = self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError(f"Tenant '{tenant_id}' no encontrado.")

        plan = tenant.plan
        mapping = {
            "PROFESSIONAL": ("quota_professional", "Profesional"),
            "LOGISTICS":    ("quota_logistics",    "Logística"),
            "FINANCE":      ("quota_finance",       "Finanzas"),
            "CRM":          ("quota_crm",           "CRM"),
        }
        resultado = []
        for code, (quota_attr, label) in mapping.items():
            lt = self.license_repo.get_license_type_by_code(code)
            if not lt:
                continue
            quota = getattr(plan, quota_attr, 0)
            used = self.license_repo.count_active_licenses_by_type(tenant_id, lt.id)
            resultado.append({
                "license_type": label,
                "code": code,
                "quota": quota,
                "used": used,
                "available": quota - used,
            })
        return resultado

    def asignar_licencia(
        self, data: AssignLicenseRequest, assigned_by: uuid.UUID
    ) -> UserCompanyLicense:
        """
        Asigna una licencia a un usuario en una compañía.
        Solo puede ejecutarlo un SuperUsuario Profesional.
        Valida que no se exceda la cuota del tenant.
        """
        assigner = self.user_repo.get_by_id(assigned_by)
        self._validar_superusuario_profesional(assigner)

        user = self.user_repo.get_by_id(data.user_id)
        if not user:
            raise NotFoundError(f"Usuario '{data.user_id}' no encontrado.")

        company = self.company_repo.get_by_id(data.company_id)
        if not company:
            raise NotFoundError(f"Compañía '{data.company_id}' no encontrada.")

        # Mismo tenant
        if user.tenant_id != company.tenant_id:
            raise BusinessRuleError("El usuario y la compañía deben pertenecer al mismo tenant.")

        lt = self.license_repo.get_license_type_by_code(data.license_type_code)
        if not lt:
            raise NotFoundError(f"Tipo de licencia '{data.license_type_code}' no existe.")

        # ¿Ya tiene esta licencia en esta compañía?
        existing = self.license_repo.get_assignment(data.user_id, data.company_id, lt.id)
        if existing and existing.is_active:
            raise ConflictError("El usuario ya tiene esta licencia en esta compañía.")

        # Verificar cuota del tenant
        tenant = self.tenant_repo.get_by_id(user.tenant_id)
        quota_map = {
            "PROFESSIONAL": tenant.plan.quota_professional,
            "LOGISTICS":    tenant.plan.quota_logistics,
            "FINANCE":      tenant.plan.quota_finance,
            "CRM":          tenant.plan.quota_crm,
        }
        quota = quota_map.get(data.license_type_code, 0)
        used = self.license_repo.count_active_licenses_by_type(user.tenant_id, lt.id)
        if used >= quota:
            raise BusinessRuleError(
                f"Cuota de licencias '{lt.name}' agotada. "
                f"El plan permite {quota} y ya hay {used} asignadas."
            )

        if existing:
            existing.is_active = True
            self.db.commit()
            return existing

        assignment = UserCompanyLicense(
            user_id=data.user_id,
            company_id=data.company_id,
            license_type_id=lt.id,
            granted_by=assigned_by,
        )
        return self.license_repo.create_assignment(assignment)

    def revocar_licencia(
        self, user_id: uuid.UUID, company_id: uuid.UUID,
        license_type_code: str, revoked_by: uuid.UUID
    ) -> None:
        revoker = self.user_repo.get_by_id(revoked_by)
        self._validar_superusuario_profesional(revoker)

        lt = self.license_repo.get_license_type_by_code(license_type_code)
        if not lt:
            raise NotFoundError(f"Tipo de licencia '{license_type_code}' no existe.")

        assignment = self.license_repo.get_assignment(user_id, company_id, lt.id)
        if not assignment or not assignment.is_active:
            raise NotFoundError("La licencia no está asignada a este usuario en esta compañía.")

        self.license_repo.revoke_assignment(assignment)

    def _validar_superusuario_profesional(self, user: TenantUser | None) -> None:
        if not user:
            raise BusinessRuleError("Usuario no encontrado.")
        if not user.is_superuser:
            raise BusinessRuleError("Se requiere flag SuperUsuario para esta operación.")
        licenses = self.license_repo.get_user_licenses_in_company.__func__  # check via DB
        # Verificar que tiene al menos una licencia PROFESSIONAL activa
        lt_prof = self.license_repo.get_license_type_by_code("PROFESSIONAL")
        if not lt_prof:
            raise BusinessRuleError("Tipo de licencia PROFESSIONAL no encontrado.")
        # Buscar en todas las compañías si tiene licencia professional
        from sqlalchemy import and_
        has_prof = (
            self.db.query(UserCompanyLicense)
            .filter(
                and_(
                    UserCompanyLicense.user_id == user.id,
                    UserCompanyLicense.license_type_id == lt_prof.id,
                    UserCompanyLicense.is_active == True,  # noqa: E712
                )
            )
            .first()
        )
        if not has_prof:
            raise BusinessRuleError("Se requiere licencia Profesional para esta operación.")


class PermissionService:
    def __init__(self, db: Session):
        self.db = db
        self.perm_repo = PermissionRepository(db)
        self.license_repo = LicenseRepository(db)
        self.user_repo = UserRepository(db)

    def listar_objetos(self, module: str | None = None) -> list:
        return self.perm_repo.get_all_objects(module)

    def obtener_permisos_usuario(self, user_id: uuid.UUID, company_id: uuid.UUID) -> list[dict]:
        perms = self.perm_repo.get_user_permissions_in_company(user_id, company_id)
        resultado = []
        for p in perms:
            obj = p.permission_object
            resultado.append({
                "permission_object_code": obj.code,
                "permission_object_name": obj.name,
                "module": obj.module,
                "level": p.level,
                "level_label": PERMISSION_LABELS.get(p.level, "DESCONOCIDO"),
            })
        return resultado

    def establecer_permiso(self, data: SetPermissionRequest, set_by: uuid.UUID) -> dict:
        """
        Establece o actualiza el permiso de un usuario sobre un objeto.
        Solo SuperUsuario Profesional puede ejecutar esta operación.
        El objeto debe pertenecer a un módulo accesible por las licencias del usuario.
        """
        setter = self.user_repo.get_by_id(set_by)
        LicenseService(self.db)._validar_superusuario_profesional(setter)

        obj = self.perm_repo.get_object_by_code(data.permission_object_code)
        if not obj:
            raise NotFoundError(f"Objeto de permiso '{data.permission_object_code}' no existe.")

        # Verificar que el usuario tiene acceso al módulo del objeto
        licenses = self.license_repo.get_user_licenses_in_company(data.user_id, data.company_id)
        modules_user = set()
        for lic in licenses:
            if lic.license_type:
                for m in lic.license_type.modules_allowed.split(","):
                    modules_user.add(m.strip())

        if obj.module not in modules_user:
            raise BusinessRuleError(
                f"El usuario no tiene licencia que permita acceso al módulo '{obj.module}'."
            )

        perm = self.perm_repo.upsert_permission(
            data.user_id, data.company_id, obj.id, data.level, set_by
        )
        return {
            "permission_object_code": obj.code,
            "permission_object_name": obj.name,
            "module": obj.module,
            "level": perm.level,
            "level_label": PERMISSION_LABELS.get(perm.level, "DESCONOCIDO"),
        }
