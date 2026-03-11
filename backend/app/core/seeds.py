"""
Seeds del sistema RINKOS ERP.
Datos semilla que deben existir en toda instalación nueva.
Idempotente: puede ejecutarse múltiples veces sin duplicar datos.
"""
import uuid

from sqlalchemy.orm import Session

from app.modules.auth.models import LicenseType
from app.modules.tenants.models import SubscriptionPlan

# ─── License Types ────────────────────────────────────────────────────────────

LICENSE_TYPES = [
    {
        "code": "PROFESSIONAL",
        "name": "Profesional",
        "description": "Acceso completo a todos los módulos del sistema.",
        "modules_allowed": "accounting,ar,ap,inventory,purchasing,sales,hr,production,service,crm,tenants,auth",
    },
    {
        "code": "LOGISTICS",
        "name": "Logística",
        "description": "Acceso a módulos de inventario, compras, ventas, producción y servicio técnico.",
        "modules_allowed": "inventory,purchasing,sales,production,service",
    },
    {
        "code": "FINANCE",
        "name": "Finanzas",
        "description": "Acceso a módulos de contabilidad, cuentas por cobrar, cuentas por pagar y reportes financieros.",
        "modules_allowed": "accounting,ar,ap",
    },
    {
        "code": "CRM",
        "name": "CRM",
        "description": "Acceso a socios de negocio, oportunidades y actividades.",
        "modules_allowed": "crm,sales",
    },
]

# ─── Subscription Plans ───────────────────────────────────────────────────────

SUBSCRIPTION_PLANS = [
    {
        "code": "BASIC",
        "name": "Basic",
        "description": "Plan básico para pequeñas empresas.",
        "max_companies": 1,
        "max_users": 3,
        "quota_professional": 1,
        "quota_logistics": 0,
        "quota_finance": 1,
        "quota_crm": 1,
    },
    {
        "code": "PRO",
        "name": "Pro",
        "description": "Plan profesional para empresas en crecimiento.",
        "max_companies": 3,
        "max_users": 10,
        "quota_professional": 1,
        "quota_logistics": 2,
        "quota_finance": 1,
        "quota_crm": 2,
    },
    {
        "code": "ENTERPRISE",
        "name": "Enterprise",
        "description": "Plan empresarial sin límites operativos.",
        "max_companies": 10,
        "max_users": 50,
        "quota_professional": 3,
        "quota_logistics": 5,
        "quota_finance": 2,
        "quota_crm": 5,
    },
]


def run_seeds(db: Session) -> None:
    """Ejecuta todos los seeds. Idempotente."""
    _seed_license_types(db)
    _seed_subscription_plans(db)
    db.commit()


def _seed_license_types(db: Session) -> None:
    for data in LICENSE_TYPES:
        exists = db.query(LicenseType).filter(LicenseType.code == data["code"]).first()
        if not exists:
            db.add(LicenseType(id=uuid.uuid4(), **data))


def _seed_subscription_plans(db: Session) -> None:
    for data in SUBSCRIPTION_PLANS:
        exists = db.query(SubscriptionPlan).filter(SubscriptionPlan.code == data["code"]).first()
        if not exists:
            db.add(SubscriptionPlan(id=uuid.uuid4(), **data))
