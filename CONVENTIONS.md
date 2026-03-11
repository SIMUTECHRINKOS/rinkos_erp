# RINKOS ERP — Convenciones de Código

> Este archivo es de cumplimiento obligatorio.
> Toda contribución de código (humana o asistida por IA) debe seguir estas reglas.
> Ante cualquier duda: preguntar al desarrollador principal antes de implementar.

---

## 1. Base de Datos (PostgreSQL)

### Nomenclatura
- Tablas: `snake_case`, plural → `journal_entries`, `fiscal_periods`, `tenant_users`
- Columnas: `snake_case` → `created_at`, `tenant_id`, `entry_number`
- Índices: `idx_{tabla}_{columna}` → `idx_journal_entries_period_id`
- Foreign keys: `fk_{tabla_origen}_{tabla_destino}` → `fk_journal_lines_accounts`

### Campos obligatorios en toda tabla
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by  UUID NOT NULL  -- user_id del creador
deleted_at  TIMESTAMPTZ    -- NULL = activo (soft delete)
```

### Reglas
- **PK siempre UUID v4** — nunca enteros autoincrementales como PK (excepción: `entry_number` que es INT secuencial por empresa)
- **Soft delete siempre** — nunca DELETE físico en tablas de negocio
- **Timestamps en UTC** — siempre `TIMESTAMPTZ`, nunca `TIMESTAMP`
- **Migraciones versionadas** — todo cambio de esquema vía Alembic, nunca SQL directo en producción

---

## 2. Backend (FastAPI / Python)

### Estructura de módulo (patrón obligatorio)
```
modules/nombre_modulo/
├── __init__.py
├── router.py       # Solo routing — sin lógica de negocio
├── service.py      # Lógica de negocio — aquí viven las reglas ERP
├── models.py       # Modelos SQLAlchemy
├── schemas.py      # Schemas Pydantic (entrada/salida de API)
├── repository.py   # Queries a DB — sin lógica de negocio
└── tests/
    ├── __init__.py
    ├── test_service.py
    └── test_router.py
```

### Nomenclatura de endpoints
```
GET    /api/v1/{modulo}/{recurso}           # Lista
POST   /api/v1/{modulo}/{recurso}           # Crear
GET    /api/v1/{modulo}/{recurso}/{id}      # Detalle
PATCH  /api/v1/{modulo}/{recurso}/{id}      # Editar parcial
DELETE /api/v1/{modulo}/{recurso}/{id}      # Soft delete (nunca físico)

Ejemplos:
GET    /api/v1/accounting/accounts
POST   /api/v1/accounting/journal-entries
GET    /api/v1/accounting/journal-entries/{id}
PATCH  /api/v1/accounting/journal-entries/{id}
```

### Reglas de Python
- **Type hints obligatorios** en todas las funciones
- **Docstrings en español** para funciones de lógica de negocio
- **Excepciones con mensaje claro** — nunca `raise Exception("error")`
- **No lógica de negocio en router.py** — solo validación de entrada y llamada al service
- **No queries directas en service.py** — usar siempre el repository
- **Tests obligatorios** antes de considerar un módulo completo (cobertura mínima 80%)

### Nomenclatura Python
```python
# Clases: PascalCase
class JournalEntry:
class AccountService:

# Funciones y variables: snake_case
def create_journal_entry():
account_balance = 0

# Constantes: UPPER_SNAKE_CASE
MAX_DECIMAL_PLACES = 4
DEFAULT_CURRENCY = "DOP"

# Schemas Pydantic: PascalCase con sufijo
class JournalEntryCreate(BaseModel):
class JournalEntryResponse(BaseModel):
class JournalEntryUpdate(BaseModel):
```

---

## 3. Reglas Contables en Código (NO NEGOCIABLES)

```python
# VALIDACIÓN OBLIGATORIA antes de postear todo asiento
def validate_journal_entry(lines):
    total_debit  = sum(line.debit_lc for line in lines)
    total_credit = sum(line.credit_lc for line in lines)
    if total_debit != total_credit:
        raise AccountingError("Asiento descuadrado: débitos != créditos. Operación rechazada.")

# NUNCA modificar un asiento en estado 'posted'
# NUNCA eliminar líneas de asientos posteados
# Para corregir: crear asiento de reversión + asiento correcto nuevo

# NUNCA postear en período cerrado directamente
# Flujo: reabrir período → modificar → ejecutar cierre nuevamente
```

---

## 4. Frontend (React + TypeScript)

### Nomenclatura
- Componentes: `PascalCase` → `JournalEntryForm.tsx`, `AccountSelector.tsx`
- Hooks: `camelCase` con prefijo `use` → `useJournalEntries.ts`, `useAccounts.ts`
- Servicios API: `camelCase` con sufijo `Service` → `accountingService.ts`
- Constantes: `UPPER_SNAKE_CASE` → `API_BASE_URL`
- Archivos de estilos: mismo nombre que el componente → `JournalEntryForm.module.css`

### Estructura de módulo frontend
```
src/modules/nombre_modulo/
├── components/     # Componentes React del módulo
├── hooks/          # Custom hooks
├── services/       # Llamadas a la API
├── types/          # TypeScript types/interfaces
└── pages/          # Páginas completas (rutas)
```

### Reglas
- **TypeScript estricto** — sin `any` salvo casos justificados con comentario
- **Colores siempre desde tokens** — nunca hardcodear colores, usar variables CSS de `tokens.css`
- **Fuente siempre Lufga** — nunca otra fuente en producción
- **Componentes de UI de Ant Design Pro** — no reinventar tablas, formularios, modales
- **React Query para datos remotos** — no useState para datos de API

### Tokens de color (usar siempre estas variables)
```css
var(--rinkos-primary-dark)   /* #1c0a3f */
var(--rinkos-primary)        /* #681db7 */
var(--rinkos-gold)           /* #ffbc00 */
var(--rinkos-amber)          /* #ffa300 */
var(--rinkos-orange)         /* #ff8f00 */
var(--rinkos-gradient)       /* gradiente oficial */
```

---

## 5. Mobile (Flutter / Dart)

### Nomenclatura
- Clases: `PascalCase` → `JournalEntryScreen`, `AccountRepository`
- Variables y funciones: `camelCase` → `journalEntry`, `fetchAccounts()`
- Constantes: `kCamelCase` → `kPrimaryColor`, `kApiBaseUrl`
- Archivos: `snake_case.dart` → `journal_entry_screen.dart`

### Estructura de módulo Flutter
```
lib/modules/nombre_modulo/
├── screens/        # Pantallas (Widgets de página completa)
├── widgets/        # Widgets reutilizables del módulo
├── providers/      # State management
└── services/       # Llamadas a la API
```

### Reglas
- **Colores desde RinkosColors** — nunca hardcodear colores
- **Fuente Lufga registrada en pubspec.yaml**
- **No lógica de negocio en widgets** — solo presentación
- **flutter_svg para todos los logos**

---

## 6. Git

### Mensajes de commit (formato obligatorio)
```
tipo(alcance): descripción en español

Tipos válidos:
  feat      → nueva funcionalidad
  fix       → corrección de bug
  docs      → cambios en documentación
  refactor  → refactorización sin cambio funcional
  test      → agregar o modificar tests
  chore     → tareas de mantenimiento
  db        → cambios de esquema de base de datos
  style     → cambios de formato/estilo (no lógica)

Ejemplos:
  feat(accounting): agregar validación de asiento descuadrado
  fix(auth): corregir expiración de token JWT
  docs(context): actualizar CLAUDE_CONTEXT sesión 2026-03-11
  db(accounting): migración inicial tablas contables core
```

### Ramas
```
main          → producción (protegida)
develop       → integración
feat/{nombre} → nuevas funcionalidades
fix/{nombre}  → correcciones
```

---

*Versión: 1.0 | Proyecto: RINKOS ERP | Actualizar con cada decisión de arquitectura nueva*
