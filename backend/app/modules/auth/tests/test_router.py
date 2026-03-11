"""
Tests de endpoints — Fase 1B: Auth, Usuarios, Licencias y Permisos.

Estrategia: cliente HTTP con DB de test inyectada.
El token JWT se obtiene vía POST /auth/login real.
"""
import uuid

import pytest

from app.core.security import create_access_token, hash_password
from app.modules.auth.models import LicenseType, PermissionObject, UserCompanyLicense
from app.modules.tenants.models import Company, TenantUser

SYSTEM_USER = uuid.UUID("00000000-0000-0000-0000-000000000001")


# ─── Helpers ──────────────────────────────────────────────────────────────────

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


def assign_license(db, user_id, company_id, license_type_id):
    lic = UserCompanyLicense(
        user_id=user_id,
        company_id=company_id,
        license_type_id=license_type_id,
        granted_by=SYSTEM_USER,
    )
    db.add(lic)
    db.commit()
    db.refresh(lic)
    return lic


def make_permission_object(db, module, code, name):
    obj = PermissionObject(module=module, code=code, name=name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_token(client, email, password, company_id):
    """Obtiene JWT real via login."""
    resp = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
        "company_id": str(company_id),
    })
    assert resp.status_code == 200, f"Login falló: {resp.json()}"
    return resp.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def superuser_token(db, tenant_id, company_id, license_professional_id, client, suffix="su"):
    """Crea superusuario con licencia PROFESSIONAL y devuelve su token."""
    email = f"{suffix}@test.com"
    su = make_user(db, tenant_id, email=email, is_superuser=True)
    assign_license(db, su.id, company_id, license_professional_id)
    token = get_token(client, email, "Pass1234", company_id)
    return su, token


# ─── Login ────────────────────────────────────────────────────────────────────

class TestLoginEndpoint:

    def test_login_exitoso_200(self, client, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        user = make_user(db, tenant_con_plan.id, email="login_ok@test.com")
        assign_license(db, user.id, company.id, license_professional.id)

        resp = client.post("/api/v1/auth/login", json={
            "email": "login_ok@test.com",
            "password": "Pass1234",
            "company_id": str(company.id),
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert len(body["modules"]) > 0

    def test_login_password_incorrecto_422(self, client, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        user = make_user(db, tenant_con_plan.id, email="badpwd@test.com")
        assign_license(db, user.id, company.id, license_professional.id)

        resp = client.post("/api/v1/auth/login", json={
            "email": "badpwd@test.com",
            "password": "WrongPass",
            "company_id": str(company.id),
        })
        assert resp.status_code == 422

    def test_login_sin_licencia_422(self, client, db, seeds, tenant_con_plan):
        company = make_company(db, tenant_con_plan.id)
        make_user(db, tenant_con_plan.id, email="nolic@test.com")

        resp = client.post("/api/v1/auth/login", json={
            "email": "nolic@test.com",
            "password": "Pass1234",
            "company_id": str(company.id),
        })
        assert resp.status_code == 422


class TestMeEndpoint:

    def test_me_autenticado_200(self, client, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        user = make_user(db, tenant_con_plan.id, email="me@test.com")
        assign_license(db, user.id, company.id, license_professional.id)
        token = get_token(client, "me@test.com", "Pass1234", company.id)

        resp = client.get("/api/v1/auth/me", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["email"] == "me@test.com"

    def test_me_sin_token_401(self, client, db, seeds):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401


# ─── Usuarios ─────────────────────────────────────────────────────────────────

class TestUsuariosEndpoints:

    def test_crear_usuario_201(self, client, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        su, token = superuser_token(
            db, tenant_con_plan.id, company.id, license_professional.id, client
        )

        resp = client.post(
            f"/api/v1/auth/usuarios?tenant_id={tenant_con_plan.id}",
            json={"email": "new@test.com", "full_name": "New User", "password": "Pass1234"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        assert resp.json()["email"] == "new@test.com"

    def test_crear_usuario_sin_superuser_403(self, client, db, seeds, tenant_con_plan,
                                             license_professional):
        company = make_company(db, tenant_con_plan.id)
        normal = make_user(db, tenant_con_plan.id, email="norm@test.com")
        assign_license(db, normal.id, company.id, license_professional.id)
        token = get_token(client, "norm@test.com", "Pass1234", company.id)

        resp = client.post(
            f"/api/v1/auth/usuarios?tenant_id={tenant_con_plan.id}",
            json={"email": "x@test.com", "full_name": "X User", "password": "Pass1234"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 403

    def test_crear_usuario_email_duplicado_409(self, client, db, seeds, tenant_con_plan,
                                               license_professional):
        company = make_company(db, tenant_con_plan.id)
        su, token = superuser_token(
            db, tenant_con_plan.id, company.id, license_professional.id, client
        )
        make_user(db, tenant_con_plan.id, email="dup@test.com")

        resp = client.post(
            f"/api/v1/auth/usuarios?tenant_id={tenant_con_plan.id}",
            json={"email": "dup@test.com", "full_name": "Dup User", "password": "Pass1234"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 409

    def test_listar_usuarios_200(self, client, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        su, token = superuser_token(
            db, tenant_con_plan.id, company.id, license_professional.id, client
        )
        make_user(db, tenant_con_plan.id, email="list1@test.com")

        resp = client.get(
            f"/api/v1/auth/usuarios?tenant_id={tenant_con_plan.id}",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        emails = [u["email"] for u in resp.json()]
        assert "su@test.com" in emails
        assert "list1@test.com" in emails

    def test_actualizar_usuario_200(self, client, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        su, token = superuser_token(
            db, tenant_con_plan.id, company.id, license_professional.id, client
        )
        target = make_user(db, tenant_con_plan.id, email="upd@test.com")

        resp = client.patch(
            f"/api/v1/auth/usuarios/{target.id}",
            json={"full_name": "Nombre Nuevo"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Nombre Nuevo"

    def test_eliminar_usuario_204(self, client, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        su, token = superuser_token(
            db, tenant_con_plan.id, company.id, license_professional.id, client
        )
        target = make_user(db, tenant_con_plan.id, email="del@test.com")

        resp = client.delete(
            f"/api/v1/auth/usuarios/{target.id}",
            headers=auth_headers(token),
        )
        assert resp.status_code == 204

    def test_cambiar_password_204(self, client, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        user = make_user(db, tenant_con_plan.id, email="pwd@test.com", password="OldPass1")
        assign_license(db, user.id, company.id, license_professional.id)
        token = get_token(client, "pwd@test.com", "OldPass1", company.id)

        resp = client.post(
            f"/api/v1/auth/usuarios/{user.id}/cambiar-password",
            json={"current_password": "OldPass1", "new_password": "NewPass99"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 204

    def test_cambiar_password_otro_usuario_422(self, client, db, seeds, tenant_con_plan,
                                               license_professional):
        """Un usuario no puede cambiar la contraseña de otro."""
        company = make_company(db, tenant_con_plan.id)
        su, token = superuser_token(
            db, tenant_con_plan.id, company.id, license_professional.id, client
        )
        other = make_user(db, tenant_con_plan.id, email="other@test.com")

        resp = client.post(
            f"/api/v1/auth/usuarios/{other.id}/cambiar-password",
            json={"current_password": "Pass1234", "new_password": "NewPass99"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 422


# ─── Licencias ────────────────────────────────────────────────────────────────

class TestLicenciasEndpoints:

    def test_listar_tipos_200(self, client, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        user = make_user(db, tenant_con_plan.id, email="ltypes@test.com")
        assign_license(db, user.id, company.id, license_professional.id)
        token = get_token(client, "ltypes@test.com", "Pass1234", company.id)

        resp = client.get("/api/v1/auth/licencias/tipos", headers=auth_headers(token))
        assert resp.status_code == 200
        codes = [lt["code"] for lt in resp.json()]
        assert "PROFESSIONAL" in codes
        assert "FINANCE" in codes

    def test_resumen_licencias_200(self, client, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        user = make_user(db, tenant_con_plan.id, email="resumen@test.com")
        assign_license(db, user.id, company.id, license_professional.id)
        token = get_token(client, "resumen@test.com", "Pass1234", company.id)

        resp = client.get(
            f"/api/v1/auth/licencias/resumen/{tenant_con_plan.id}",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        prof = next(r for r in data if r["code"] == "PROFESSIONAL")
        assert prof["quota"] == 1
        assert prof["used"] == 1  # resumen@test.com ya tiene 1

    def test_asignar_licencia_201(self, client, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        su, token = superuser_token(
            db, tenant_con_plan.id, company.id, license_professional.id, client
        )
        target = make_user(db, tenant_con_plan.id, email="assign@test.com")

        resp = client.post(
            "/api/v1/auth/licencias/asignar",
            json={
                "user_id": str(target.id),
                "company_id": str(company.id),
                "license_type_code": "FINANCE",
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 201

    def test_asignar_licencia_cuota_agotada_422(self, client, db, seeds, tenant_con_plan,
                                                 license_professional):
        """Plan PRO quota_professional=1, ya usada por superusuario → 422."""
        company = make_company(db, tenant_con_plan.id)
        su, token = superuser_token(
            db, tenant_con_plan.id, company.id, license_professional.id, client
        )
        target = make_user(db, tenant_con_plan.id, email="over@test.com")

        resp = client.post(
            "/api/v1/auth/licencias/asignar",
            json={
                "user_id": str(target.id),
                "company_id": str(company.id),
                "license_type_code": "PROFESSIONAL",
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 422

    def test_revocar_licencia_204(self, client, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        su, token = superuser_token(
            db, tenant_con_plan.id, company.id, license_professional.id, client
        )
        target = make_user(db, tenant_con_plan.id, email="revoke@test.com")
        finance_lt = db.query(LicenseType).filter_by(code="FINANCE").first()
        assign_license(db, target.id, company.id, finance_lt.id)

        resp = client.post(
            "/api/v1/auth/licencias/revocar",
            params={
                "user_id": str(target.id),
                "company_id": str(company.id),
                "license_type_code": "FINANCE",
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 204


# ─── Permisos ─────────────────────────────────────────────────────────────────

class TestPermisosEndpoints:

    def test_listar_objetos_200(self, client, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        user = make_user(db, tenant_con_plan.id, email="objlist@test.com")
        assign_license(db, user.id, company.id, license_professional.id)
        token = get_token(client, "objlist@test.com", "Pass1234", company.id)
        make_permission_object(db, "accounting", "acc_balance", "Balance General")

        resp = client.get("/api/v1/auth/permisos/objetos", headers=auth_headers(token))
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_establecer_permiso_200(self, client, db, seeds, tenant_con_plan, license_professional):
        company = make_company(db, tenant_con_plan.id)
        su, token = superuser_token(
            db, tenant_con_plan.id, company.id, license_professional.id, client
        )
        obj = make_permission_object(db, "accounting", "acc_journal", "Asiento Contable")
        target = make_user(db, tenant_con_plan.id, email="perm@test.com")
        assign_license(db, target.id, company.id, license_professional.id)

        resp = client.post(
            "/api/v1/auth/permisos",
            json={
                "user_id": str(target.id),
                "company_id": str(company.id),
                "permission_object_code": "acc_journal",
                "level": 2,
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["level_label"] == "TOTAL"

    def test_establecer_permiso_sin_superuser_403(self, client, db, seeds, tenant_con_plan,
                                                   license_professional):
        company = make_company(db, tenant_con_plan.id)
        normal = make_user(db, tenant_con_plan.id, email="normperm@test.com")
        assign_license(db, normal.id, company.id, license_professional.id)
        token = get_token(client, "normperm@test.com", "Pass1234", company.id)
        make_permission_object(db, "accounting", "acc_trial", "Balance de Comprobación")

        target = make_user(db, tenant_con_plan.id, email="permt@test.com")
        assign_license(db, target.id, company.id, license_professional.id)

        resp = client.post(
            "/api/v1/auth/permisos",
            json={
                "user_id": str(target.id),
                "company_id": str(company.id),
                "permission_object_code": "acc_trial",
                "level": 1,
            },
            headers=auth_headers(token),
        )
        assert resp.status_code == 403

    def test_obtener_permisos_usuario_200(self, client, db, seeds, tenant_con_plan,
                                          license_professional):
        company = make_company(db, tenant_con_plan.id)
        su, token = superuser_token(
            db, tenant_con_plan.id, company.id, license_professional.id, client
        )
        make_permission_object(db, "accounting", "acc_ar", "Cuentas por Cobrar")
        target = make_user(db, tenant_con_plan.id, email="getperm@test.com")
        assign_license(db, target.id, company.id, license_professional.id)

        client.post(
            "/api/v1/auth/permisos",
            json={
                "user_id": str(target.id),
                "company_id": str(company.id),
                "permission_object_code": "acc_ar",
                "level": 1,
            },
            headers=auth_headers(token),
        )

        resp = client.get(
            f"/api/v1/auth/permisos/usuario/{target.id}/company/{company.id}",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        perms = resp.json()
        assert len(perms) == 1
        assert perms[0]["level_label"] == "LECTURA"
