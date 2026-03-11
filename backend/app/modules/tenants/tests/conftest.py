"""
Fixtures para tests de Fase 1A — Tenants y Companies.

Estrategia: commits reales contra rinkos_erp_test + truncado de tablas entre tests.
Esto garantiza que los queries dentro del service vean los datos ya insertados,
evitando inconsistencias por rollback en medio de una transacción.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.modules.tenants.models import SubscriptionPlan

TEST_DATABASE_URL = "postgresql://macmini@localhost:5432/rinkos_erp_test"

engine_test = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Crea las tablas una vez para toda la sesión de tests."""
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(autouse=True)
def limpiar_tablas():
    """Trunca todas las tablas entre tests para garantizar aislamiento."""
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
    """Sesión de DB por test con commits reales."""
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture()
def client():
    """Cliente HTTP con la DB de test inyectada (sesión propia por request)."""
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def plan_basic(db) -> SubscriptionPlan:
    plan = SubscriptionPlan(
        id=uuid.uuid4(),
        code="BASIC",
        name="Basic",
        description="Plan básico",
        max_companies=1,
        max_users=5,
        is_active=True,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@pytest.fixture()
def plan_pro(db) -> SubscriptionPlan:
    plan = SubscriptionPlan(
        id=uuid.uuid4(),
        code="PRO",
        name="Pro",
        description="Plan profesional",
        max_companies=5,
        max_users=20,
        is_active=True,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan
