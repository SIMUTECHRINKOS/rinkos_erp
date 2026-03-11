"""Tests de lógica de negocio — TenantService y CompanyService."""
import uuid

import pytest

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.modules.tenants.schemas import CompanyCreate, TenantCreate, TenantUpdate
from app.modules.tenants.service import CompanyService, TenantService


class TestTenantService:
    def test_crear_tenant_exitoso(self, db, plan_basic):
        data = TenantCreate(
            code="ACME01",
            name="ACME Corp",
            email="admin@acme.com",
            plan_id=plan_basic.id,
        )
        tenant = TenantService(db).crear_tenant(data)
        assert tenant.id is not None
        assert tenant.code == "ACME01"
        assert tenant.email == "admin@acme.com"

    def test_crear_tenant_code_duplicado_falla(self, db, plan_basic):
        data = TenantCreate(
            code="DUPL01",
            name="Empresa A",
            email="a@empresa.com",
            plan_id=plan_basic.id,
        )
        TenantService(db).crear_tenant(data)
        data2 = TenantCreate(
            code="DUPL01",
            name="Empresa B",
            email="b@empresa.com",
            plan_id=plan_basic.id,
        )
        with pytest.raises(ConflictError):
            TenantService(db).crear_tenant(data2)

    def test_crear_tenant_email_duplicado_falla(self, db, plan_basic):
        data = TenantCreate(
            code="EMP001",
            name="Empresa A",
            email="mismo@email.com",
            plan_id=plan_basic.id,
        )
        TenantService(db).crear_tenant(data)
        data2 = TenantCreate(
            code="EMP002",
            name="Empresa B",
            email="mismo@email.com",
            plan_id=plan_basic.id,
        )
        with pytest.raises(ConflictError):
            TenantService(db).crear_tenant(data2)

    def test_crear_tenant_plan_inexistente_falla(self, db):
        data = TenantCreate(
            code="EMP003",
            name="Empresa C",
            email="c@empresa.com",
            plan_id=uuid.uuid4(),
        )
        with pytest.raises(NotFoundError):
            TenantService(db).crear_tenant(data)

    def test_obtener_tenant_inexistente_falla(self, db):
        with pytest.raises(NotFoundError):
            TenantService(db).obtener_tenant(uuid.uuid4())

    def test_actualizar_tenant(self, db, plan_basic):
        data = TenantCreate(
            code="UPD001",
            name="Original",
            email="upd@empresa.com",
            plan_id=plan_basic.id,
        )
        tenant = TenantService(db).crear_tenant(data)
        actualizado = TenantService(db).actualizar_tenant(
            tenant.id, TenantUpdate(name="Actualizado")
        )
        assert actualizado.name == "Actualizado"

    def test_eliminar_tenant_soft_delete(self, db, plan_basic):
        data = TenantCreate(
            code="DEL001",
            name="Para Borrar",
            email="del@empresa.com",
            plan_id=plan_basic.id,
        )
        tenant = TenantService(db).crear_tenant(data)
        TenantService(db).eliminar_tenant(tenant.id)
        with pytest.raises(NotFoundError):
            TenantService(db).obtener_tenant(tenant.id)


class TestCompanyService:
    def _crear_tenant(self, db, plan, code: str, email: str):
        data = TenantCreate(
            code=code, name=f"Tenant {code}", email=email, plan_id=plan.id
        )
        return TenantService(db).crear_tenant(data)

    def test_crear_company_exitosa(self, db, plan_pro):
        tenant = self._crear_tenant(db, plan_pro, "TPRO01", "pro@test.com")
        data = CompanyCreate(
            code="COMP01",
            name="Mi Empresa",
            currency_lc="DOP",
            currency_sy="USD",
            inventory_method="AVG",
        )
        company = CompanyService(db).crear_company(tenant.id, data)
        assert company.id is not None
        assert company.schema_name == "rinkos_comp01"
        assert company.settings_locked is False

    def test_crear_company_supera_limite_plan_falla(self, db, plan_basic):
        """Plan Basic permite solo 1 empresa — la segunda debe fallar."""
        tenant = self._crear_tenant(db, plan_basic, "TBASIC1", "basic@test.com")
        data1 = CompanyCreate(code="CMP001", name="Empresa 1", currency_lc="DOP", currency_sy="USD")
        CompanyService(db).crear_company(tenant.id, data1)

        data2 = CompanyCreate(code="CMP002", name="Empresa 2", currency_lc="DOP", currency_sy="USD")
        with pytest.raises(BusinessRuleError):
            CompanyService(db).crear_company(tenant.id, data2)

    def test_crear_company_code_duplicado_falla(self, db, plan_pro):
        tenant = self._crear_tenant(db, plan_pro, "TPRO02", "pro2@test.com")
        data = CompanyCreate(code="DUPCO1", name="Empresa", currency_lc="DOP", currency_sy="USD")
        CompanyService(db).crear_company(tenant.id, data)
        with pytest.raises(ConflictError):
            CompanyService(db).crear_company(tenant.id, data)

    def test_modificar_moneda_con_settings_locked_falla(self, db, plan_pro):
        """Bloqueo técnico: no se puede cambiar moneda si ya hay movimientos contables."""
        from app.modules.tenants.schemas import CompanyUpdate
        tenant = self._crear_tenant(db, plan_pro, "TPRO03", "pro3@test.com")
        data = CompanyCreate(code="LOCKCO", name="Empresa Lock", currency_lc="DOP", currency_sy="USD")
        company = CompanyService(db).crear_company(tenant.id, data)

        # Simular bloqueo (primer asiento posteado)
        company.settings_locked = True
        db.flush()

        with pytest.raises(BusinessRuleError):
            CompanyService(db).actualizar_company(
                company.id, CompanyUpdate(currency_lc="EUR")
            )
