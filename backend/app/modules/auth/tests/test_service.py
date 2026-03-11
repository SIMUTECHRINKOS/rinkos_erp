"""
Tests de servicios — Fase 1B: Auth, Usuarios, Licencias y Permisos.

Cubre:
  - AuthService.login()
  - UserService (CRUD + cambio de password)
  - LicenseService (asignar, revocar, resumen, validar cuota)
  - PermissionService (establecer permiso, validar módulo)
"""
import uuid

import pytest

from app.core.security import hash_password
from app.modules.auth.models import LicenseType, PermissionObject, UserCompanyLicense
from app.modules.auth.schemas import (
    AssignLicenseRequest,
    LoginRequest,
    SetPermissionRequest,
    UserCreate,
    UserPasswordChange,
    UserUpdate,
)
from app.modules.auth.service import AuthService, LicenseService, PermissionService, UserService
from app.modules.tenants.models import Company, TenantUser


# ─── Helpers ──────────────────────────────────────────────────────────────────

SYSTEM_USER = uuid.UUID("00000000-0000-0000-0000-000000000001")


def make_user(db, tenant_id, email="user@test.com", is_superuser=False, password="Pass1234"):
    u = TenantUser(
        tenant_id=tenant_id,
        email=email,
        full_name="Test User",
        hashed_password=hash_password(password),
        is_superuser=is_superuser,
        created_by=SYSTEM_USER,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def make_company(db, tenant_id, code="COMP01"):
    c = Company(
        tenant_id=tenant_id,
        code=code,
        name="Test Company",
        currency_lc="DOP",
        currency_sy="USD",
        schema_name=f"rinkos_{code.lower()}",
        created_by=SYSTEM_USER,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def assign_license(db, user_id, company_id, license_type_id, granted_by=SYSTEM_USER):
    lic = UserCompanyLicense(
        user_id=user_id,
        company_id=company_id,
        license_type_id=license_type_id,
        granted_by=granted_by,
    )
    db.add(lic)
    db.commit()
    db.refresh(lic)
    return lic


def make_permission_object(db, module="sales", code="sales_invoice", name="Factura de Venta"):
    obj = PermissionObject(module=module, code=code, name=name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ─── AuthService ──────────────────────────────────────────────────────────────

class TestAuthServiceLogin:

    def test_login_exitoso(self, db, seeds, tenant_con_plan, license_professional):
        """Login correcto devuelve token con módulos del tipo de licencia."""
        company = make_company(db, tenant_con_plan.id)
        user = make_user(db, tenant_con_plan.id, email="login@test.com")
        assign_license(db, user.id, company.id, license_professional.id)

        result = AuthService(db).login(LoginRequest(
            email="login@test.com",
            password="Pass1234",
            company_id=company.id,
        ))

        assert result.access_token
        assert result.user_id == user.id
        assert result.company_id == company.id
        assert "accounting" in result.modules

    def test_login_password_incorrecto(self, db, seeds, tenant_con_plan, license_professional):
        """Credenciales incorrectas lanzan BusinessRuleError."""
        from app.core.exceptions import BusinessRuleError
        company = make_company(db, tenant_con_plan.id)
        user = make_user(db, tenant_con_plan.id, email="bad@test.com")
        assign_license(db, user.id, company.id, license_professional.id)

        with pytest.raises(BusinessRuleError, match="Credenciales"):
            AuthService(db).login(LoginRequest(
                email="bad@test.com",
                password="WrongPass",
                company_id=company.id,
            ))

    def test_login_usuario_inactivo(self, db, seeds, tenant_con_plan, license_professional):
        """Usuario inactivo no puede iniciar sesión."""
        from app.core.exceptions import BusinessRuleError
        company = make_company(db, tenant_con_plan.id)
        user = make_user(db, tenant_con_plan.id, email="inactive@test.com")
        user.is_active = False
        db.commit()
        assign_license(db, user.id, company.id, license_professional.id)

        with pytest.raises(BusinessRuleError, match="inactivo"):
            AuthService(db).login(LoginRequest(
                email="inactive@test.com",
                password="Pass1234",
                company_id=company.id,
            ))

    def test_login_sin_licencia(self, db, seeds, tenant_con_plan):
        """Usuario sin licencias en la compañía no puede hacer login."""
        from app.core.exceptions import BusinessRuleError
        company = make_company(db, tenant_con_plan.id)
        make_user(db, tenant_con_plan.id, email="nolic@test.com")

        with pytest.raises(BusinessRuleError, match="licencias"):
            AuthService(db).login(LoginRequest(
                email="nolic@test.com",
                password="Pass1234",
                company_id=company.id,
            ))

    def test_login_modulos_union_de_licencias(self, db, seeds, tenant_con_plan,
                                               license_professional, license_finance):
        """Con dos licencias activas, los módulos son la unión de ambas."""
        company = make_company(db, tenant_con_plan.id)
        user = make_user(db, tenant_con_plan.id, email="multi@test.com")
        assign_license(db, user.id, company.id, license_professional.id)
        assign_license(db, user.id, company.id, license_finance.id)

        result = AuthService(db).login(LoginRequest(
            email="multi@test.com",
            password="Pass1234",
            company_id=company.id,
        ))
        # PROFESSIONAL ya incluye accounting, ar, ap — no deben duplicarse
        assert result.modules == sorted(set(result.modules))


# ─── UserService ──────────────────────────────────────────────────────────────

class TestUserService:

    def test_crear_usuario_exitoso(self, db, seeds, tenant_con_plan):
        svc = UserService(db)
        data = UserCreate(
            email="nuevo@test.com",
            full_name="Nuevo Usuario",
            password="SecurePass1",
        )
        user = svc.crear_usuario(tenant_con_plan.id, data)

        assert user.id
        assert user.email == "nuevo@test.com"
        assert user.tenant_id == tenant_con_plan.id
        assert not user.is_superuser

    def test_crear_usuario_email_duplicado(self, db, seeds, tenant_con_plan):
        from app.core.exceptions import ConflictError
        make_user(db, tenant_con_plan.id, email="dup@test.com")
        svc = UserService(db)
        with pytest.raises(ConflictError):
            svc.crear_usuario(tenant_con_plan.id, UserCreate(
                email="dup@test.com",
                full_name="Otro Usuario",
                password="SecurePass1",
            ))

    def test_crear_usuario_tenant_inexistente(self, db, seeds):
        from app.core.exceptions import NotFoundError
        svc = UserService(db)
        with pytest.raises(NotFoundError):
            svc.crear_usuario(uuid.uuid4(), UserCreate(
                email="nobody@test.com",
                full_name="Nadie",
                password="SecurePass1",
            ))

    def test_listar_usuarios_por_tenant(self, db, seeds, tenant_con_plan):
        make_user(db, tenant_con_plan.id, email="u1@test.com")
        make_user(db, tenant_con_plan.id, email="u2@test.com")
        users = UserService(db).listar_usuarios(tenant_con_plan.id)
        assert len(users) == 2

    def test_actualizar_usuario(self, db, seeds, tenant_con_plan):
        user = make_user(db, tenant_con_plan.id, email="upd@test.com")
        updated = UserService(db).actualizar_usuario(
            user.id,
            UserUpdate(full_name="Nombre Actualizado"),
        )
        assert updated.full_name == "Nombre Actualizado"

    def test_actualizar_usuario_no_encontrado(self, db, seeds):
        from app.core.exceptions import NotFoundError
        with pytest.raises(NotFoundError):
            UserService(db).actualizar_usuario(uuid.uuid4(), UserUpdate(full_name="No Existe"))

    def test_cambiar_password_exitoso(self, db, seeds, tenant_con_plan):
        user = make_user(db, tenant_con_plan.id, email="pwd@test.com", password="OldPass1")
        UserService(db).cambiar_password(user.id, "OldPass1", "NewPass99")
        # Verificar que la nueva password funciona
        from app.core.security import verify_password
        db.refresh(user)
        assert verify_password("NewPass99", user.hashed_password)

    def test_cambiar_password_actual_incorrecta(self, db, seeds, tenant_con_plan):
        from app.core.exceptions import BusinessRuleError
        user = make_user(db, tenant_con_plan.id, email="pwdfail@test.com", password="OldPass1")
        with pytest.raises(BusinessRuleError, match="incorrecta"):
            UserService(db).cambiar_password(user.id, "WrongOld", "NewPass99")

    def test_eliminar_usuario_soft_delete(self, db, seeds, tenant_con_plan):
        user = make_user(db, tenant_con_plan.id, email="del@test.com")
        UserService(db).eliminar_usuario(user.id)
        db.refresh(user)
        assert user.deleted_at is not None

    def test_eliminar_usuario_no_encontrado(self, db, seeds):
        from app.core.exceptions import NotFoundError
        with pytest.raises(NotFoundError):
            UserService(db).eliminar_usuario(uuid.uuid4())


# ─── LicenseService ───────────────────────────────────────────────────────────

class TestLicenseService:

    def _make_superuser_profesional(self, db, tenant_id, company_id, license_professional):
        """Crea un superusuario con licencia PROFESSIONAL en la compañía dada."""
        su = make_user(db, tenant_id, email="super@test.com", is_superuser=True)
        assign_license(db, su.id, company_id, license_professional.id)
        return su

    def test_listar_tipos_licencia(self, db, seeds):
        tipos = LicenseService(db).listar_tipos()
        codes = [t.code for t in tipos]
        assert "PROFESSIONAL" in codes
        assert "FINANCE" in codes
        assert len(tipos) == 4

    def test_resumen_licencias_tenant(self, db, seeds, tenant_con_plan):
        resumen = LicenseService(db).resumen_licencias_tenant(tenant_con_plan.id)
        prof = next(r for r in resumen if r["code"] == "PROFESSIONAL")
        assert prof["quota"] == 1  # PRO plan: 1 profesional
        assert prof["used"] == 0

    def test_resumen_tenant_inexistente(self, db, seeds):
        from app.core.exceptions import NotFoundError
        with pytest.raises(NotFoundError):
            LicenseService(db).resumen_licencias_tenant(uuid.uuid4())

    def test_asignar_licencia_exitoso(self, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        su = self._make_superuser_profesional(db, tenant_con_plan.id, company.id, license_professional)

        target = make_user(db, tenant_con_plan.id, email="target@test.com")
        # El plan PRO tiene quota_professional=1 y ya hay 1 (el superusuario)
        # Usamos FINANCE que tiene quota=1 y 0 usadas
        license_finance = db.query(LicenseType).filter_by(code="FINANCE").first()
        result = LicenseService(db).asignar_licencia(
            AssignLicenseRequest(
                user_id=target.id,
                company_id=company.id,
                license_type_code="FINANCE",
            ),
            assigned_by=su.id,
        )
        assert result.user_id == target.id
        assert result.is_active

    def test_asignar_licencia_cuota_agotada(self, db, seeds, tenant_con_plan, license_professional):
        """El plan PRO tiene quota_professional=1. Asignar una segunda falla."""
        company = make_company(db, tenant_con_plan.id)
        from app.core.exceptions import BusinessRuleError
        su = self._make_superuser_profesional(db, tenant_con_plan.id, company.id, license_professional)

        # La cuota PROFESSIONAL del plan PRO es 1 y ya está usada por el superusuario
        target = make_user(db, tenant_con_plan.id, email="over@test.com")
        with pytest.raises(BusinessRuleError, match="Cuota"):
            LicenseService(db).asignar_licencia(
                AssignLicenseRequest(
                    user_id=target.id,
                    company_id=company.id,
                    license_type_code="PROFESSIONAL",
                ),
                assigned_by=su.id,
            )

    def test_asignar_licencia_duplicada(self, db, seeds, tenant_con_plan, license_professional):
        """Asignar la misma licencia dos veces al mismo usuario/compañía falla."""
        from app.core.exceptions import ConflictError
        company = make_company(db, tenant_con_plan.id)
        su = self._make_superuser_profesional(db, tenant_con_plan.id, company.id, license_professional)

        # LOGISTICS tiene quota=2 en plan PRO → podemos asignar 2 sin problema
        target = make_user(db, tenant_con_plan.id, email="dup2@test.com")
        LicenseService(db).asignar_licencia(
            AssignLicenseRequest(
                user_id=target.id,
                company_id=company.id,
                license_type_code="LOGISTICS",
            ),
            assigned_by=su.id,
        )
        with pytest.raises(ConflictError):
            LicenseService(db).asignar_licencia(
                AssignLicenseRequest(
                    user_id=target.id,
                    company_id=company.id,
                    license_type_code="LOGISTICS",
                ),
                assigned_by=su.id,
            )

    def test_asignar_sin_ser_superusuario(self, db, seeds, tenant_con_plan, license_professional):
        """Un usuario normal no puede asignar licencias."""
        from app.core.exceptions import BusinessRuleError
        company = make_company(db, tenant_con_plan.id)
        normal = make_user(db, tenant_con_plan.id, email="normal@test.com")
        assign_license(db, normal.id, company.id, license_professional.id)

        target = make_user(db, tenant_con_plan.id, email="target2@test.com")
        with pytest.raises(BusinessRuleError, match="SuperUsuario"):
            LicenseService(db).asignar_licencia(
                AssignLicenseRequest(
                    user_id=target.id,
                    company_id=company.id,
                    license_type_code="CRM",
                ),
                assigned_by=normal.id,
            )

    def test_revocar_licencia_exitoso(self, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        su = self._make_superuser_profesional(db, tenant_con_plan.id, company.id, license_professional)

        target = make_user(db, tenant_con_plan.id, email="revoke@test.com")
        assign_license(db, target.id, company.id,
                       db.query(LicenseType).filter_by(code="FINANCE").first().id)

        LicenseService(db).revocar_licencia(target.id, company.id, "FINANCE", su.id)
        lic = db.query(UserCompanyLicense).filter_by(
            user_id=target.id, company_id=company.id
        ).first()
        assert lic.is_active is False

    def test_revocar_licencia_inexistente(self, db, seeds, tenant_con_plan, license_professional):
        from app.core.exceptions import NotFoundError
        company = make_company(db, tenant_con_plan.id)
        su = self._make_superuser_profesional(db, tenant_con_plan.id, company.id, license_professional)

        target = make_user(db, tenant_con_plan.id, email="norev@test.com")
        with pytest.raises(NotFoundError):
            LicenseService(db).revocar_licencia(target.id, company.id, "FINANCE", su.id)


# ─── PermissionService ────────────────────────────────────────────────────────

class TestPermissionService:

    def _setup_superuser(self, db, tenant_id, company_id, license_professional):
        su = make_user(db, tenant_id, email="psuper@test.com", is_superuser=True)
        assign_license(db, su.id, company_id, license_professional.id)
        return su

    def test_listar_objetos_permiso(self, db, seeds):
        make_permission_object(db, module="sales", code="invoice_list", name="Lista Facturas")
        make_permission_object(db, module="inventory", code="item_master", name="Maestro Artículos")
        objetos = PermissionService(db).listar_objetos()
        assert len(objetos) >= 2

    def test_listar_objetos_filtrar_por_modulo(self, db, seeds):
        make_permission_object(db, module="hr", code="hr_employee", name="Empleado")
        make_permission_object(db, module="hr", code="hr_payroll", name="Nómina")
        make_permission_object(db, module="sales", code="sales_order2", name="Orden Venta")
        objetos = PermissionService(db).listar_objetos(module="hr")
        assert all(o.module == "hr" for o in objetos)
        assert len(objetos) == 2

    def test_establecer_permiso_exitoso(self, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        su = self._setup_superuser(db, tenant_con_plan.id, company.id, license_professional)

        # accounting está en los módulos de PROFESSIONAL
        obj = make_permission_object(db, module="accounting", code="journal_entry", name="Asiento")

        target = make_user(db, tenant_con_plan.id, email="perm_target@test.com")
        assign_license(db, target.id, company.id, license_professional.id)

        result = PermissionService(db).establecer_permiso(
            SetPermissionRequest(
                user_id=target.id,
                company_id=company.id,
                permission_object_code="journal_entry",
                level=2,
            ),
            set_by=su.id,
        )
        assert result["level"] == 2
        assert result["level_label"] == "TOTAL"

    def test_establecer_permiso_modulo_no_accesible(self, db, seeds, tenant_con_plan,
                                                     license_professional):
        """Setear permiso en módulo al que el usuario no tiene licencia falla."""
        from app.core.exceptions import BusinessRuleError
        company = make_company(db, tenant_con_plan.id)
        su = self._setup_superuser(db, tenant_con_plan.id, company.id, license_professional)

        # CRM tiene módulos: crm, sales
        # El target solo tiene licencia FINANCE (accounting, ar, ap)
        obj = make_permission_object(db, module="crm", code="crm_opportunity", name="Oportunidad")
        finance_lt = db.query(LicenseType).filter_by(code="FINANCE").first()
        target = make_user(db, tenant_con_plan.id, email="no_crm@test.com")
        assign_license(db, target.id, company.id, finance_lt.id)

        with pytest.raises(BusinessRuleError, match="módulo"):
            PermissionService(db).establecer_permiso(
                SetPermissionRequest(
                    user_id=target.id,
                    company_id=company.id,
                    permission_object_code="crm_opportunity",
                    level=1,
                ),
                set_by=su.id,
            )

    def test_actualizar_permiso_upsert(self, db, seeds, tenant_con_plan, license_professional):
        """Llamar dos veces actualiza el nivel (upsert)."""
        company = make_company(db, tenant_con_plan.id)
        su = self._setup_superuser(db, tenant_con_plan.id, company.id, license_professional)
        obj = make_permission_object(db, module="accounting", code="acc_report", name="Reporte Contable")
        target = make_user(db, tenant_con_plan.id, email="upsert@test.com")
        assign_license(db, target.id, company.id, license_professional.id)

        PermissionService(db).establecer_permiso(
            SetPermissionRequest(
                user_id=target.id,
                company_id=company.id,
                permission_object_code="acc_report",
                level=1,
            ),
            set_by=su.id,
        )
        result = PermissionService(db).establecer_permiso(
            SetPermissionRequest(
                user_id=target.id,
                company_id=company.id,
                permission_object_code="acc_report",
                level=2,
            ),
            set_by=su.id,
        )
        assert result["level"] == 2

    def test_obtener_permisos_usuario(self, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        su = self._setup_superuser(db, tenant_con_plan.id, company.id, license_professional)
        make_permission_object(db, module="accounting", code="acc_ledger", name="Libro Mayor")
        target = make_user(db, tenant_con_plan.id, email="get_perm@test.com")
        assign_license(db, target.id, company.id, license_professional.id)

        PermissionService(db).establecer_permiso(
            SetPermissionRequest(
                user_id=target.id,
                company_id=company.id,
                permission_object_code="acc_ledger",
                level=1,
            ),
            set_by=su.id,
        )

        perms = PermissionService(db).obtener_permisos_usuario(target.id, company.id)
        assert len(perms) == 1
        assert perms[0]["level_label"] == "LECTURA"
