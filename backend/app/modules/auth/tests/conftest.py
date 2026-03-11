"""Fixtures para tests de Fase 1B — Auth, Usuarios, Licencias y Permisos."""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core.seeds import run_seeds
from app.main import app
from app.modules.auth.models import LicenseType
from app.modules.tenants.models import SubscriptionPlan, Tenant

TEST_DATABASE_URL = "postgresql://macmini@localhost:5432/rinkos_erp_test"
engine_test = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(autouse=True)
def limpiar_tablas():
    yield
    session = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    finally:
        session.close()


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture()
def client():
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def seeds(db):
    """Carga los seeds base (planes + tipos de licencia)."""
    run_seeds(db)
    return db


@pytest.fixture()
def plan_pro(seeds) -> SubscriptionPlan:
    return seeds.query(SubscriptionPlan).filter_by(code="PRO").first()


@pytest.fixture()
def license_professional(seeds) -> LicenseType:
    return seeds.query(LicenseType).filter_by(code="PROFESSIONAL").first()


@pytest.fixture()
def license_finance(seeds) -> LicenseType:
    return seeds.query(LicenseType).filter_by(code="FINANCE").first()


@pytest.fixture()
def tenant_con_plan(seeds, plan_pro) -> Tenant:
    tenant = Tenant(
        id=uuid.uuid4(),
        code="TAUTH01",
        name="Tenant Auth Test",
        email="auth@test.com",
        plan_id=plan_pro.id,
        created_by=uuid.UUID("00000000-0000-0000-0000-000000000001"),
    )
    seeds.add(tenant)
    seeds.commit()
    seeds.refresh(tenant)
    return tenant
