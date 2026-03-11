"""Tests de endpoints HTTP — Tenants y Companies."""
import uuid


class TestTenantRouter:
    def test_listar_planes(self, client, plan_basic, plan_pro):
        resp = client.get("/api/v1/tenants/planes")
        assert resp.status_code == 200
        codigos = [p["code"] for p in resp.json()]
        assert "BASIC" in codigos
        assert "PRO" in codigos

    def test_crear_tenant_201(self, client, plan_basic):
        resp = client.post("/api/v1/tenants/", json={
            "code": "HTTP01",
            "name": "HTTP Tenant",
            "email": "http@test.com",
            "plan_id": str(plan_basic.id),
        })
        assert resp.status_code == 201
        assert resp.json()["code"] == "HTTP01"

    def test_crear_tenant_code_duplicado_409(self, client, plan_basic):
        payload = {"code": "DUP409", "name": "Duplicado", "email": "dup409@test.com", "plan_id": str(plan_basic.id)}
        client.post("/api/v1/tenants/", json=payload)
        resp = client.post("/api/v1/tenants/", json={**payload, "email": "otro@test.com"})
        assert resp.status_code == 409

    def test_obtener_tenant_inexistente_404(self, client):
        resp = client.get(f"/api/v1/tenants/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_actualizar_tenant_200(self, client, plan_basic):
        crear = client.post("/api/v1/tenants/", json={
            "code": "PATCH01",
            "name": "Original",
            "email": "patch01@test.com",
            "plan_id": str(plan_basic.id),
        })
        tid = crear.json()["id"]
        resp = client.patch(f"/api/v1/tenants/{tid}", json={"name": "Actualizado"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Actualizado"

    def test_eliminar_tenant_204(self, client, plan_basic):
        crear = client.post("/api/v1/tenants/", json={
            "code": "DEL204",
            "name": "Para Borrar",
            "email": "del204@test.com",
            "plan_id": str(plan_basic.id),
        })
        tid = crear.json()["id"]
        resp = client.delete(f"/api/v1/tenants/{tid}")
        assert resp.status_code == 204
        assert client.get(f"/api/v1/tenants/{tid}").status_code == 404


class TestCompanyRouter:
    def _tenant(self, client, plan, code: str, email: str) -> str:
        resp = client.post("/api/v1/tenants/", json={
            "code": code, "name": f"T {code}", "email": email, "plan_id": str(plan.id)
        })
        return resp.json()["id"]

    def test_crear_company_201(self, client, plan_pro):
        tid = self._tenant(client, plan_pro, "CRCO01", "crco01@test.com")
        resp = client.post(f"/api/v1/tenants/{tid}/companies", json={
            "code": "EMP001",
            "name": "Mi Empresa",
            "currency_lc": "DOP",
            "currency_sy": "USD",
        })
        assert resp.status_code == 201
        assert resp.json()["schema_name"] == "rinkos_emp001"

    def test_crear_company_supera_limite_422(self, client, plan_basic):
        """Plan Basic = 1 empresa máximo."""
        tid = self._tenant(client, plan_basic, "CRCO02", "crco02@test.com")
        client.post(f"/api/v1/tenants/{tid}/companies", json={
            "code": "LIMEMP1", "name": "E1", "currency_lc": "DOP", "currency_sy": "USD"
        })
        resp = client.post(f"/api/v1/tenants/{tid}/companies", json={
            "code": "LIMEMP2", "name": "E2", "currency_lc": "DOP", "currency_sy": "USD"
        })
        assert resp.status_code == 422

    def test_listar_companies_200(self, client, plan_pro):
        tid = self._tenant(client, plan_pro, "CRCO03", "crco03@test.com")
        client.post(f"/api/v1/tenants/{tid}/companies", json={
            "code": "LISTCO1", "name": "E1", "currency_lc": "DOP", "currency_sy": "USD"
        })
        resp = client.get(f"/api/v1/tenants/{tid}/companies")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
