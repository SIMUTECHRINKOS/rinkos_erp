# Fase 1A — Multi-Tenant + Companies

## Estado: COMPLETADO — 2026-03-11

---

## Alcance

Implementación de la estructura multi-tenant base de RINKOS ERP.
Cubre la jerarquía: Tenant → Companies y los planes de suscripción.

---

## Tablas creadas (schema `public`)

| Tabla                | Descripción                                              |
|----------------------|----------------------------------------------------------|
| `subscription_plans` | Planes de suscripción (seeds: Basic / Pro / Enterprise)  |
| `tenants`            | Organizaciones clientes                                  |
| `companies`          | Empresas dentro de cada tenant (1..N por tenant)         |
| `tenant_users`       | Usuarios del sistema (credenciales auth en Fase 1B)      |
| `user_company_access`| Acceso de usuarios a empresas específicas                |
| `audit_log`          | Registro de auditoría global (inmutable)                 |

---

## Endpoints implementados

```
GET    /api/v1/tenants/planes                          → Lista planes activos
GET    /api/v1/tenants/planes/{plan_id}                → Detalle de plan

GET    /api/v1/tenants/                                → Lista tenants
POST   /api/v1/tenants/                                → Crear tenant
GET    /api/v1/tenants/{tenant_id}                     → Detalle tenant
PATCH  /api/v1/tenants/{tenant_id}                     → Actualizar tenant
DELETE /api/v1/tenants/{tenant_id}                     → Soft delete tenant

GET    /api/v1/tenants/{tenant_id}/companies           → Lista companies del tenant
POST   /api/v1/tenants/{tenant_id}/companies           → Crear company
GET    /api/v1/tenants/{tenant_id}/companies/{id}      → Detalle company
PATCH  /api/v1/tenants/{tenant_id}/companies/{id}      → Actualizar company
DELETE /api/v1/tenants/{tenant_id}/companies/{id}      → Soft delete company
```

---

## Reglas de negocio implementadas

1. **Límite de empresas por plan**: un tenant no puede tener más companies que `plan.max_companies`. Error 422 si se supera.
2. **Código único global**: `tenant.code` y `company.code` son únicos en todo el sistema. Error 409 si hay duplicado.
3. **Email único de tenant**: `tenant.email` es único. Error 409 si hay duplicado.
4. **Schema por company**: al crear una company se genera automáticamente el schema PostgreSQL `rinkos_{company_code}`.
5. **Bloqueo de configuraciones**: si `company.settings_locked = True`, no se pueden modificar `currency_lc`, `currency_sy` ni `inventory_method`. Este flag lo activa el motor contable al postear el primer asiento (Fase 2B).
6. **Soft delete**: ninguna tabla usa DELETE físico. Se marca `deleted_at`.

---

## Archivos creados

```
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py          # Settings desde .env
│   │   ├── database.py        # Engine, SessionLocal, Base, get_db
│   │   └── exceptions.py      # Excepciones y helpers HTTP
│   ├── shared/
│   │   └── base_model.py      # TimestampMixin
│   └── modules/tenants/
│       ├── models.py           # SQLAlchemy models
│       ├── schemas.py          # Pydantic schemas
│       ├── repository.py       # Queries DB
│       ├── service.py          # Lógica de negocio
│       ├── router.py           # Endpoints FastAPI
│       └── tests/
│           ├── conftest.py
│           ├── test_service.py  # 11 tests
│           └── test_router.py   # 9 tests
├── migrations/
│   └── versions/aa492d082e73_fase_1a_schema_public_inicial.py
├── requirements.txt
├── pytest.ini
├── alembic.ini
└── .env.example
```

---

## Tests: 20/20 pasando

```
TestTenantService  →  7 tests
TestCompanyService →  4 tests
TestTenantRouter   →  6 tests
TestCompanyRouter  →  3 tests
```

---

## Pendiente para fases siguientes

- **Fase 1B**: Agregar `hashed_password` a `tenant_users` + endpoints de auth JWT
- **Fase 2B**: El motor contable activa `settings_locked = True` al postear el primer asiento
- **Seeds**: Insertar planes Basic / Pro / Enterprise en producción (script de seed pendiente)
- **Portal admin**: Gestión de contratos y planes (fuera del MVP)
