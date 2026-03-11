"""
Script de datos de desarrollo — RINKOS ERP
Crea un tenant, una compañía, un superusuario y un usuario normal
con licencias asignadas para probar el login.

Uso:
    cd backend
    source .venv/bin/activate
    python scripts/seed_dev.py
"""
import sys
import uuid
sys.path.insert(0, ".")  # permite importar app/ desde backend/

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.core.seeds import run_seeds
from app.modules.auth.models import LicenseType, UserCompanyLicense
from app.modules.tenants.models import Company, SubscriptionPlan, Tenant, TenantUser

SYSTEM_USER = uuid.UUID("00000000-0000-0000-0000-000000000001")

def main():
    db = SessionLocal()
    try:
        # 1. Seeds base (planes + tipos de licencia)
        run_seeds(db)
        print("✓ Seeds base aplicados")

        # 2. Verificar que no existan ya los datos
        if db.query(Tenant).filter_by(code="DEMO01").first():
            print("⚠ Los datos de desarrollo ya existen. Nada que hacer.")
            return

        # 3. Tenant demo
        plan = db.query(SubscriptionPlan).filter_by(code="PRO").first()
        tenant = Tenant(
            id=uuid.uuid4(),
            code="DEMO01",
            name="RINKOS Demo",
            email="demo@rinkos.com",
            plan_id=plan.id,
            created_by=SYSTEM_USER,
        )
        db.add(tenant)
        db.flush()
        print(f"✓ Tenant creado: {tenant.name} (ID: {tenant.id})")

        # 4. Compañía demo
        company = Company(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            code="DEMO01",
            name="Empresa Demo S.A.",
            country="DOM",
            currency_lc="DOP",
            currency_sy="USD",
            schema_name="rinkos_demo01",
            created_by=SYSTEM_USER,
        )
        db.add(company)
        db.flush()
        print(f"✓ Compañía creada: {company.name} (ID: {company.id})")

        # 5. SuperUsuario con licencia PROFESSIONAL
        lt_prof = db.query(LicenseType).filter_by(code="PROFESSIONAL").first()
        superuser = TenantUser(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email="super@test.com",
            full_name="Super Usuario Demo",
            hashed_password=hash_password("Pass1234"),
            is_superuser=True,
            created_by=SYSTEM_USER,
        )
        db.add(superuser)
        db.flush()
        db.add(UserCompanyLicense(
            user_id=superuser.id,
            company_id=company.id,
            license_type_id=lt_prof.id,
            granted_by=SYSTEM_USER,
        ))
        print(f"✓ SuperUsuario creado: {superuser.email}")

        # 6. Usuario normal con licencia FINANCE
        lt_finance = db.query(LicenseType).filter_by(code="FINANCE").first()
        user = TenantUser(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email="user@test.com",
            full_name="Usuario Demo",
            hashed_password=hash_password("Pass1234"),
            is_superuser=False,
            created_by=SYSTEM_USER,
        )
        db.add(user)
        db.flush()
        db.add(UserCompanyLicense(
            user_id=user.id,
            company_id=company.id,
            license_type_id=lt_finance.id,
            granted_by=SYSTEM_USER,
        ))
        print(f"✓ Usuario normal creado: {user.email}")

        db.commit()
        print("\n✅ Datos de desarrollo listos.")
        print("─────────────────────────────────────")
        print(f"  SuperUsuario : super@test.com / Pass1234")
        print(f"  Usuario      : user@test.com  / Pass1234")
        print(f"  Compañía     : Empresa Demo S.A.")
        print("─────────────────────────────────────")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
