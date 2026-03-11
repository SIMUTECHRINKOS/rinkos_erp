# Fase 1B — Auth + Usuarios + Licencias + Permisos

## Estado: COMPLETADO — 2026-03-11

---

## Alcance

Implementación del sistema de autenticación JWT y el modelo de licencias y permisos de RINKOS ERP.
Inspirado en SAP Business One: 4 tipos de licencia con módulos diferenciados, permisos granulares por objeto.

---

## Tablas creadas (schema `public`)

| Tabla                    | Descripción                                                      |
|--------------------------|------------------------------------------------------------------|
| `license_types`          | 4 tipos semilla: PROFESSIONAL, LOGISTICS, FINANCE, CRM           |
| `user_company_licenses`  | Licencias asignadas a usuario por compañía                       |
| `permission_objects`     | Catálogo de objetos/funciones configurables (se puebla por módulo)|
| `user_permissions`       | Nivel de permiso (0/1/2) por usuario por objeto por compañía     |

### Columnas agregadas a tablas existentes

| Tabla               | Columna           | Descripción                       |
|---------------------|-------------------|-----------------------------------|
| `tenant_users`      | `hashed_password` | Contraseña hasheada con bcrypt    |
| `subscription_plans`| `quota_professional` | Cuota de licencias PROFESSIONAL|
| `subscription_plans`| `quota_logistics`    | Cuota de licencias LOGISTICS   |
| `subscription_plans`| `quota_finance`      | Cuota de licencias FINANCE     |
| `subscription_plans`| `quota_crm`          | Cuota de licencias CRM         |

---

## Seeds

### Tipos de Licencia

| Code         | Módulos accesibles                                                          |
|--------------|-----------------------------------------------------------------------------|
| PROFESSIONAL | accounting, ar, ap, inventory, purchasing, sales, hr, production, service, crm, tenants, auth |
| LOGISTICS    | inventory, purchasing, sales, production, service                           |
| FINANCE      | accounting, ar, ap                                                          |
| CRM          | crm, sales                                                                  |

### Cuotas por Plan

| Plan       | PROFESSIONAL | LOGISTICS | FINANCE | CRM |
|------------|:---:|:---:|:---:|:---:|
| Basic      |  1  |  0  |  1  |  1  |
| Pro        |  1  |  2  |  1  |  2  |
| Enterprise |  3  |  5  |  2  |  5  |

---

## Endpoints implementados

```
POST   /api/v1/auth/login                                   → Login JWT
GET    /api/v1/auth/me                                      → Usuario autenticado

GET    /api/v1/auth/usuarios?tenant_id=                     → Listar usuarios del tenant
POST   /api/v1/auth/usuarios?tenant_id=                     → Crear usuario (SuperUsuario)
PATCH  /api/v1/auth/usuarios/{user_id}                      → Actualizar usuario (SuperUsuario)
POST   /api/v1/auth/usuarios/{user_id}/cambiar-password      → Cambiar contraseña (propio usuario)
DELETE /api/v1/auth/usuarios/{user_id}                      → Soft delete (SuperUsuario)

GET    /api/v1/auth/licencias/tipos                         → Listar tipos de licencia
GET    /api/v1/auth/licencias/resumen/{tenant_id}           → Uso vs cuota del tenant
POST   /api/v1/auth/licencias/asignar                       → Asignar licencia (SuperUsuario Prof.)
POST   /api/v1/auth/licencias/revocar                       → Revocar licencia (SuperUsuario Prof.)

GET    /api/v1/auth/permisos/objetos?module=               → Listar objetos de permiso
GET    /api/v1/auth/permisos/usuario/{user_id}/company/{id} → Permisos de usuario en compañía
POST   /api/v1/auth/permisos                                → Establecer/actualizar permiso (SuperUsuario Prof.)
```

---

## Reglas de negocio implementadas

1. **Login con licencia**: Solo puede autenticarse un usuario que tenga al menos una licencia activa en la compañía seleccionada.
2. **Módulos del JWT**: El token incluye la unión de todos los módulos de las licencias activas del usuario en esa compañía.
3. **SuperUsuario Profesional**: Solo un usuario con `is_superuser=True` + licencia PROFESSIONAL activa puede asignar/revocar licencias y configurar permisos.
4. **Cuota de licencias**: No se puede asignar una licencia si el tenant ya agotó el cupo de ese tipo según su plan. Error 422.
5. **Permisos por módulo**: Solo se puede configurar un permiso sobre un objeto si el usuario destinatario tiene licencia que incluya el módulo del objeto. Error 422.
6. **Niveles de permiso**: 0=NINGUNO, 1=LECTURA, 2=TOTAL. Upsert: si ya existe, actualiza el nivel.
7. **Soft delete en usuarios**: `deleted_at` se marca, el usuario queda inactivo.
8. **Cambio de contraseña**: Solo el propio usuario puede cambiar su contraseña. Error 422 si la contraseña actual es incorrecta.

---

## Archivos creados / modificados

```
backend/
├── app/
│   ├── core/
│   │   ├── security.py         # hash_password, verify_password, JWT encode/decode
│   │   ├── dependencies.py     # CurrentUser, get_current_user, require_superuser, require_module
│   │   └── seeds.py            # Seeds idempotentes: LicenseType + SubscriptionPlan
│   └── modules/auth/
│       ├── models.py           # LicenseType, UserCompanyLicense, PermissionObject, UserPermission
│       ├── schemas.py          # LoginRequest, TokenResponse, UserCreate/Update, AssignLicenseRequest...
│       ├── repository.py       # UserRepository, LicenseRepository, PermissionRepository
│       ├── service.py          # AuthService, UserService, LicenseService, PermissionService
│       ├── router.py           # 14 endpoints FastAPI
│       └── tests/
│           ├── conftest.py     # Fixtures: seeds, plan_pro, license_*, tenant_con_plan
│           ├── test_service.py # 30 tests de servicios
│           └── test_router.py  # 22 tests de endpoints
├── migrations/versions/
│   └── b50a547b7c7e_fase_1b_auth_licencias_permisos.py
└── requirements.txt            # bcrypt==4.0.1 (compatible con passlib 1.7.4)
```

### Módulos modificados de Fase 1A
- `modules/tenants/models.py` → `TenantUser.hashed_password`, cuotas en `SubscriptionPlan`
- `modules/tenants/schemas.py` → `CompanyUpdate` con `currency_lc`, `currency_sy`, `inventory_method`
- `main.py` → versión 0.2.0, incluye auth_router, seeds en lifespan

---

## Tests: 52/52 pasando

```
TestAuthServiceLogin    →  5 tests
TestUserService         → 10 tests
TestLicenseService      →  8 tests
TestPermissionService   →  7 tests
─────────────────────────────────
TestLoginEndpoint       →  3 tests
TestMeEndpoint          →  2 tests
TestUsuariosEndpoints   →  7 tests
TestLicenciasEndpoints  →  5 tests
TestPermisosEndpoints   →  4 tests
─────────────────────────────────
TOTAL: 52 tests — 52 passed
```

---

## Notas técnicas

- **bcrypt==4.0.1** requerido: `bcrypt>=5.0.0` es incompatible con `passlib==1.7.4` (API `__about__` eliminada).
- **Módulos accesibles** = unión de `modules_allowed` de todas las licencias activas del usuario en la compañía.
- **`_validar_superusuario_profesional`** consulta directamente la DB para verificar licencia PROFESSIONAL activa (no depende del JWT).
- **`permission_objects`** se puebla módulo a módulo durante el desarrollo; en Fase 1B no hay objetos predefinidos (solo los que los tests crean).

---

## Pendiente para fases siguientes

- **Fase 2A**: Módulo de Contabilidad — chart of accounts, journals, períodos fiscales.
- **Fase 2B**: Motor de asientos contables — activará `settings_locked=True` al postear el primer asiento.
- **Seeds de permission_objects**: Se agregarán a medida que se implementan los módulos operativos.
