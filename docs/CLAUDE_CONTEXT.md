# RINKOS ERP — DOCUMENTO MAESTRO DE CONTEXTO
## Archivo de inicio obligatorio para cada sesión de Claude Code

---

## ⚠️ REGLAS ABSOLUTAS DE COLABORACIÓN — LEER ANTES DE CUALQUIER ACCIÓN

```
REGLA 0: Este proyecto se llama RINKOS ERP. Siempre usar este nombre.
REGLA 1: NUNCA asumir, inventar, ni inferir reglas de negocio ERP.
          Ante cualquier duda de lógica de negocio → PREGUNTAR PRIMERO.
REGLA 2: Siempre responder y documentar en ESPAÑOL.
REGLA 3: El desarrollador tiene +20 años de experiencia en SAP Business One.
          Claude asiste. El desarrollador decide. Siempre.
REGLA 4: Toda sugerencia técnica se valida contra este documento antes de implementar.
REGLA 5: NUNCA cambiar el modelo de datos contable sin aprobación explícita.
REGLA 6: Este documento se actualiza al cerrar cada sesión de trabajo.
REGLA 7: La carta gráfica y paleta de colores RINKOS es provista por el cliente.
          NUNCA usar colores o estilos propios sin tener la carta gráfica aprobada.
```

---

## A. IDENTIDAD VISUAL — CARTA GRÁFICA OFICIAL RINKOS ERP

### Paleta de Colores
| Rol en el Sistema       | Pantone   | HEX       | RGB              | Uso Principal                               |
|-------------------------|-----------|-----------|------------------|---------------------------------------------|
| Primario oscuro         | 2765 C    | `#1c0a3f` | 28, 10, 63       | Fondos navbar, sidebar, headers, texto dark  |
| Primario medio          | 267 C     | `#681db7` | 104, 29, 183     | Botones primarios, links, acentos, íconos   |
| Acento dorado           | 7549 C    | `#ffbc00` | 255, 188, 0      | Inicio gradiente del símbolo, badges         |
| Acento ámbar            | 2013 C    | `#ffa300` | 255, 163, 0      | Letra K del logo, estados, highlights        |
| Acento naranja          | 137 C     | `#ff8f00` | 255, 143, 0      | Fin del gradiente, warnings, secundario      |

### Gradiente Oficial del Símbolo
```css
linear-gradient(90deg, #ffbc00 0%, #ffb300 29%, #ff9b00 77%, #ff8f00 97%)
```

### Tipografía
| Peso           | Uso           |
|----------------|---------------|
| Lufga Black    | Logo / marca  |
| Lufga SemiBold | Títulos H1    |
| Lufga Light    | Subtítulos H2 |

> Lufga debe estar en /frontend/public/fonts/ y /mobile/assets/fonts/ como archivo local (.woff2 / .ttf)

### Variantes de Logo (SVG — todos en /docs/brand/)
| Archivo             | Descripción                                              | Uso Recomendado                        |
|---------------------|----------------------------------------------------------|----------------------------------------|
| LOGO_RINKOS-01.svg  | Logo completo: símbolo arriba + texto abajo (cuadrado)   | Splash screen, login, presentaciones   |
| LOGO_RINKOS-02.svg  | Solo símbolo / ícono (C con gradiente dorado) — grande   | Favicon, app icon, loading             |
| LOGO_RINKOS-03.svg  | Solo wordmark — texto RINKOS sin símbolo                 | Emails, uso horizontal mínimo          |
| LOGO_RINKOS-04.svg  | Horizontal: símbolo izquierda + texto derecha            | Navbar web, header de documentos       |
| LOGO_RINKOS-05.svg  | Horizontal: texto izquierda + símbolo derecha            | Variante alternativa horizontal        |

### Tokens CSS (React)
```css
:root {
  --rinkos-primary-dark:  #1c0a3f;
  --rinkos-primary:       #681db7;
  --rinkos-gold:          #ffbc00;
  --rinkos-amber:         #ffa300;
  --rinkos-orange:        #ff8f00;
  --rinkos-gradient:      linear-gradient(90deg, #ffbc00 0%, #ffb300 29%, #ff9b00 77%, #ff8f00 97%);
  --rinkos-text-on-dark:  #ffffff;
  --rinkos-text-primary:  #1c0a3f;
  --rinkos-bg-light:      #f5f3fa;
  --rinkos-surface:       #ffffff;
}
```

### Tokens Dart (Flutter)
```dart
class RinkosColors {
  static const primaryDark = Color(0xFF1C0A3F);
  static const primary     = Color(0xFF681DB7);
  static const gold        = Color(0xFFFFBC00);
  static const amber       = Color(0xFFFFA300);
  static const orange      = Color(0xFFFF8F00);
  static const textOnDark  = Color(0xFFFFFFFF);
  static const textPrimary = Color(0xFF1C0A3F);
  static const bgLight     = Color(0xFFF5F3FA);
  static const surface     = Color(0xFFFFFFFF);
}
```

---


## B. REGLAS DE NEGOCIO CONFIRMADAS

> Estas reglas fueron definidas explícitamente por el desarrollador.
> NUNCA modificar sin su aprobación. Se irán agregando módulo a módulo.

### B.1 — Reglas del Motor Multimoneda

```
ESTRUCTURA DE MONEDAS (3 capas obligatorias en todo documento y asiento):

  total_lc  →  Moneda Local (LC)     — Moneda principal de la empresa. SIEMPRE presente.
  total_sy  →  Moneda del Sistema (SY) — Moneda secundaria global. SIEMPRE presente.
  total_fc  →  Moneda Extranjera (FC) — Solo presente si el documento se emite en moneda
                                        distinta a LC y SY.

CONFIGURACIÓN DE MONEDAS:
  - Existe un maestro de monedas a nivel de sistema (tabla global).
  - Por empresa se configura: cuál es su LC y cuál es su SY.
  - LC y SY pueden ser cualquier combinación (DOP/USD, COP/USD, EUR/GBP, etc.).
  - El sistema es 100% configurable para cualquier país.
  - Después de LC y SY pueden existir N monedas extranjeras adicionales.

BLOQUEO CRÍTICO — configuraciones selladas al postear el PRIMER asiento:
  - Moneda Local (LC): NO modificable una vez hay movimiento contable.
  - Moneda del Sistema (SY): NO modificable una vez hay movimiento contable.
  - El bloqueo es técnico en el backend — no una advertencia, es un rechazo.
```

### B.2 — Reglas de Valorización de Inventario

```
MÉTODOS DISPONIBLES: Promedio Ponderado y FIFO (a elección en configuración inicial).
  - Configurable por empresa al momento de la configuración del sistema.
  - Solo estas dos opciones en el MVP.

BLOQUEO CRÍTICO — configuración sellada al postear el PRIMER asiento:
  - Método de valorización: NO modificable una vez hay movimiento contable.
  - El bloqueo es técnico en el backend — no una advertencia, es un rechazo.
```

### B.3 — Reglas del Número de Asiento Contable

```
FORMATO: Entero (INT) autoincremental, secuencial por empresa.
  - Un solo contador por empresa, no por tipo ni por período.
  - No se reinicia al cambiar de período ni de año fiscal.
  - Un número asignado NUNCA se reutiliza, aunque el asiento sea cancelado.
  - El número cancelado queda en el historial como registro de auditoría.
```

### B.4 — Reglas de Estados de Período Contable

```
ESTADOS VÁLIDOS DE UN PERÍODO:
  1. Abierto          → Acepta todo tipo de asientos.
  2. Abierto para ventas → Acepta solo asientos de módulo de ventas (facturación).
                          Útil para mantener el período abierto solo para ajustes de AR.
  3. Cerrado          → No acepta asientos directamente.

REGLA DE MODIFICACIÓN EN PERÍODO CERRADO:
  - Es posible modificar asientos de un período cerrado.
  - Flujo obligatorio: Reabrir período → Modificar → Ejecutar cierre nuevamente.
  - El cierre de período no es automático: es un proceso que el usuario debe ejecutar.
  - El sistema debe registrar en auditoría cada vez que un período se reabre.
```

### B.5 — Principio General de Bloqueos de Negocio

```
REGLA MAESTRA:
  Existen configuraciones del sistema que quedan selladas de forma permanente
  una vez que existe el primer movimiento contable o transaccional relacionado.
  Estos bloqueos se definen y documentan módulo a módulo durante el desarrollo.
  NUNCA implementar un bloqueo sin haberlo consultado y confirmado con el desarrollador.
  NUNCA levantar un bloqueo ya definido sin aprobación explícita del desarrollador.
```

---

## 1. IDENTIDAD DEL PROYECTO

| Campo               | Valor                                               |
|---------------------|-----------------------------------------------------|
| **Nombre**          | RINKOS ERP                                          |
| **Tipo**            | Plataforma ERP SaaS multidispositivo                |
| **Mercado**         | PYMES latinoamericanas                              |
| **Modelo SaaS**     | Híbrido (multi-tenant configurable por cliente)     |
| **Horizonte**       | Por fases sin fecha fija                            |
| **Carta gráfica**   | COMPLETADA — ver Sección A de este documento        |
| **Paleta colores**  | COMPLETADA — ver Sección A de este documento        |
| **Idioma sistema**  | Español (primario) + multilenguaje futuro           |
| **Referencia ERP**  | SAP Business One + Odoo (mejores prácticas)         |
| **Desarrollador**   | Solo / Claude Code como par de programación         |

---

## 2. PRINCIPIO RECTOR ARQUITECTÓNICO

```
LA CONTABILIDAD ES LA COLUMNA VERTEBRAL DE RINKOS ERP.

- Toda transacción operativa genera asientos contables automáticos.
- Si la contabilidad no puede registrar el evento → el evento NO ocurre.
- El plan de cuentas es el esquema unificador de todo el sistema.
- Ningún módulo operativo puede existir sin el motor contable activo.
- Las reglas de negocio contables SIEMPRE se consultan con el desarrollador.
```

---

## 3. STACK TECNOLÓGICO APROBADO

### Backend
| Tecnología         | Uso                                    | Versión   |
|--------------------|----------------------------------------|-----------|
| Python             | Lenguaje principal backend             | 3.12+     |
| FastAPI            | Framework API REST                     | Última    |
| SQLAlchemy         | ORM                                    | 2.0+      |
| Alembic            | Migraciones de base de datos           | Última    |
| Pytest             | Testing unitario y de integración      | Última    |
| WeasyPrint         | Generación de PDFs (facturas, reportes)| Última    |
| Redis              | Cache + cola de trabajos async         | 7+        |

### Base de Datos
| Tecnología         | Uso                                    | Notas     |
|--------------------|----------------------------------------|-----------|
| PostgreSQL         | Base de datos principal                | 16+       |
| Supabase           | Host PostgreSQL + Auth + Realtime      | Cloud     |
| Schema-per-tenant  | Modelo de aislamiento multi-tenant     | Ver Sec.7 |

### Frontend Web
| Tecnología         | Uso                                    | Versión   |
|--------------------|----------------------------------------|-----------|
| React              | Framework UI web                       | 18+       |
| Vite               | Bundler / Dev server                   | Última    |
| Ant Design Pro     | Componentes ERP empresariales          | Última    |
| Zustand            | Estado global                          | Última    |
| React Query        | Cache y sincronización de datos        | Última    |

### Mobile
| Tecnología         | Uso                                    | Versión   |
|--------------------|----------------------------------------|-----------|
| Flutter            | App móvil iOS + Android                | 3.x       |
| Dart               | Lenguaje Flutter                       | Última    |

### Infraestructura
| Servicio           | Uso                          | Costo estimado  |
|--------------------|------------------------------|-----------------|
| Render             | Backend FastAPI + Redis      | $7-25/mes       |
| Render             | PostgreSQL (base de datos)   | $7-20/mes       |
| Vercel             | Frontend React               | $0 inicio       |
| GitHub             | Repositorio + CI/CD Actions  | $0              |

---

## 4. ESTRUCTURA DEL MONOREPO

```
rinkos-erp/
├── backend/                   # FastAPI
│   ├── app/
│   │   ├── core/              # Config, seguridad, DB session
│   │   ├── modules/           # Un directorio por módulo ERP
│   │   │   ├── accounting/    # Motor contable — PRIMERO
│   │   │   ├── auth/          # Autenticación y usuarios
│   │   │   ├── tenants/       # Multi-tenant
│   │   │   ├── ar/            # Cuentas por Cobrar
│   │   │   ├── ap/            # Cuentas por Pagar
│   │   │   ├── inventory/     # Inventario
│   │   │   ├── purchasing/    # Compras
│   │   │   ├── sales/         # Ventas + CRM
│   │   │   ├── hr/            # RRHH + Nómina
│   │   │   ├── production/    # Producción + MRP
│   │   │   └── service/       # Servicio Técnico
│   │   ├── shared/            # Modelos base, utils, excepciones
│   │   └── main.py
│   ├── migrations/            # Alembic
│   ├── tests/
│   └── requirements.txt
│
├── frontend/                  # React + Vite
│   ├── src/
│   │   ├── modules/           # Espeja estructura del backend
│   │   ├── shared/            # Componentes reutilizables
│   │   ├── layouts/
│   │   └── main.tsx
│   └── package.json
│
├── mobile/                    # Flutter
│   ├── lib/
│   │   ├── modules/
│   │   ├── shared/
│   │   └── main.dart
│   └── pubspec.yaml
│
├── docs/                      # Documentación
│   ├── CLAUDE_CONTEXT.md      # ESTE ARCHIVO — actualizar siempre
│   ├── ERD/                   # Diagramas entidad-relación
│   ├── API/                   # Especificaciones de endpoints
│   └── modules/               # Especificación funcional por módulo
│
├── infra/                     # Scripts de infraestructura
│   ├── railway/
│   └── supabase/
│
├── CONVENTIONS.md             # Convenciones de código obligatorias
└── README.md
```

---

## 5. CONVENCIONES DE CÓDIGO

### Nomenclatura de tablas PostgreSQL
```
- Tablas en snake_case y plural: journal_entries, fiscal_periods
- Columnas en snake_case: created_at, tenant_id, entry_number
- Claves primarias: siempre UUID v4, columna "id"
- Foreign keys: nombre_tabla_id (ej: account_id, period_id)
- Timestamps obligatorios en toda tabla: created_at, updated_at, created_by
- Soft delete: columna deleted_at (NULL = activo)
```

### Nomenclatura de endpoints FastAPI
```
/api/v1/{módulo}/{recurso}
Ejemplos:
  GET    /api/v1/accounting/accounts
  POST   /api/v1/accounting/journal-entries
  GET    /api/v1/accounting/journal-entries/{id}
  PATCH  /api/v1/accounting/journal-entries/{id}
```

### Estructura de módulo backend (patrón obligatorio)
```
modules/nombre_modulo/
├── router.py      # Endpoints FastAPI
├── service.py     # Lógica de negocio
├── models.py      # Modelos SQLAlchemy
├── schemas.py     # Schemas Pydantic (entrada/salida API)
├── repository.py  # Queries a DB
└── tests/
    ├── test_service.py
    └── test_router.py
```

### Reglas de asientos contables (código)
```python
# SIEMPRE validar antes de postear:
assert sum(debits) == sum(credits), "Asiento descuadrado — operación rechazada"

# NUNCA modificar un asiento en estado 'posted'
# NUNCA eliminar líneas de journal_entry_lines de asientos posteados
# Para corregir: crear asiento de reversión + asiento correcto
```

---

## 6. MODELO DE DATOS CONTABLE CORE

> ⚠️ Estas tablas son inmutables en estructura salvo aprobación explícita del desarrollador.
> Toda modificación requiere migración Alembic versionada.

### Tablas en schema de cada tenant

```sql
-- Plan de Cuentas (equivale a OACT en SAP B1)
accounts (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code            VARCHAR(20) NOT NULL UNIQUE,
  name            VARCHAR(200) NOT NULL,
  type            VARCHAR(1) NOT NULL,  -- A=Activo, P=Pasivo, E=Patrimonio, I=Ingreso, X=Egreso, C=Costo
  nature          VARCHAR(2) NOT NULL,  -- Dr=Deudora, Cr=Acreedora
  parent_id       UUID REFERENCES accounts(id),
  level           INTEGER NOT NULL,
  is_posting      BOOLEAN DEFAULT true, -- false = cuenta cabecera
  currency        VARCHAR(3) DEFAULT 'USD',
  is_reconcilable BOOLEAN DEFAULT false,
  is_control      BOOLEAN DEFAULT false,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW(),
  created_by      UUID NOT NULL,
  deleted_at      TIMESTAMPTZ
)

-- Períodos Contables (equivale a OPRD en SAP B1)
fiscal_periods (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        VARCHAR(50) NOT NULL,
  start_date  DATE NOT NULL,
  end_date    DATE NOT NULL,
  status      VARCHAR(10) DEFAULT 'open',  -- open, closed, locked
  fiscal_year INTEGER NOT NULL,
  period_num  INTEGER NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  created_by  UUID NOT NULL
)

-- Cabecera de Asiento (equivale a OJDT en SAP B1)
journal_entries (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entry_number    VARCHAR(20) NOT NULL UNIQUE,
  entry_date      DATE NOT NULL,
  period_id       UUID REFERENCES fiscal_periods(id),
  reference       VARCHAR(100),
  memo            TEXT,
  type            VARCHAR(20) NOT NULL, -- manual, system, opening, closing, reversal
  status          VARCHAR(10) DEFAULT 'draft', -- draft, posted, cancelled
  currency        VARCHAR(3) NOT NULL,
  exchange_rate   DECIMAL(18,6) DEFAULT 1.0,
  source_module   VARCHAR(50),   -- 'sales', 'purchasing', 'hr', etc.
  source_doc_id   UUID,          -- ID del documento origen
  reversal_of     UUID REFERENCES journal_entries(id),
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW(),
  created_by      UUID NOT NULL
)

-- Líneas de Asiento (equivale a JDT1 en SAP B1)
journal_entry_lines (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entry_id         UUID REFERENCES journal_entries(id) ON DELETE RESTRICT,
  line_num         INTEGER NOT NULL,
  account_id       UUID REFERENCES accounts(id),
  debit            DECIMAL(18,4) DEFAULT 0,
  credit           DECIMAL(18,4) DEFAULT 0,
  debit_currency   DECIMAL(18,4) DEFAULT 0,
  credit_currency  DECIMAL(18,4) DEFAULT 0,
  cost_center_id   UUID,
  project_id       UUID,
  memo             VARCHAR(200),
  due_date         DATE,
  created_at       TIMESTAMPTZ DEFAULT NOW()
)

-- Tipos de cambio
exchange_rates (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  from_currency VARCHAR(3) NOT NULL,
  to_currency   VARCHAR(3) NOT NULL,
  rate_date     DATE NOT NULL,
  rate          DECIMAL(18,6) NOT NULL,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(from_currency, to_currency, rate_date)
)
```

---

## 7. MODELO MULTI-TENANT

```
Schema 'public' (sistema):
  - tenants
  - tenant_users
  - subscription_plans
  - audit_log

Schema 'rinkos_{tenant_code}' (por empresa):
  - accounts, fiscal_periods, journal_entries, journal_entry_lines
  - [todos los módulos operativos]

Regla: search_path se establece por sesión según tenant_id del JWT.
```

---

## 8. MAPA DE MÓDULOS Y FASES

| Fase | Módulo                     | Prerequisito          | Estado     |
|------|----------------------------|-----------------------|------------|
| 0    | Fundación / Monorepo       | —                     | PENDIENTE  |
| 1A   | Multi-Tenant + Empresas    | Fase 0                | PENDIENTE  |
| 1B   | Auth + Usuarios + Roles    | Fase 1A               | PENDIENTE  |
| 2A   | Plan de Cuentas + Períodos | Fase 1 completa       | PENDIENTE  |
| 2B   | Motor de Asientos (Diario) | Fase 2A               | PENDIENTE  |
| 2C   | Reportes Financieros Core  | Fase 2B               | PENDIENTE  |
| 3A   | Cuentas por Cobrar (AR)    | Fase 2 completa       | PENDIENTE  |
| 3B   | Cuentas por Pagar (AP)     | Fase 2 completa       | PENDIENTE  |
| 4A   | Inventario / Almacenes     | Fase 3B               | PENDIENTE  |
| 4B   | Compras                    | Fases 3B + 4A         | PENDIENTE  |
| 5A   | Ventas + CRM               | Fases 3A + 4A         | PENDIENTE  |
| 6    | RRHH + Nómina              | Fase 2 + 1B           | PENDIENTE  |
| 7    | Producción + MRP           | Fases 4A + 5A         | PENDIENTE  |
| 8    | Servicio Técnico           | Fases 4A + 5A         | PENDIENTE  |
| 9    | Integraciones + API Pública| Fases 3-6 estables    | PENDIENTE  |
| M    | App Flutter (paralelo)     | Desde Fase 3 en adelante| PENDIENTE|

---

## 9. DECISIONES TÉCNICAS REGISTRADAS

| Fecha      | Decisión                                           | Motivo / Detalle                                              |
|------------|----------------------------------------------------|---------------------------------------------------------------|
| 2026-03-11 | Stack: FastAPI + PostgreSQL + React/Vite + Flutter | Ecosistema, costo, dominio actual del desarrollador |
| 2026-03-11 | Infraestructura: Render (backend + PostgreSQL) + Vercel | <$200/mes inicio. Supabase descartado. |
| 2026-03-11 | Multi-tenant: schema-per-tenant PostgreSQL | Aislamiento total + costo |
| 2026-03-11 | Contabilidad como eje central, no módulo opcional | Principio arquitectónico SAP B1 |
| 2026-03-11 | Carta gráfica y logos RINKOS recibidos | Paleta oficial + 5 variantes SVG — ver Sección A |
| 2026-03-11 | País de lanzamiento inicial: República Dominicana | Confirmado por referencia a DGII. Sistema 100% configurable para cualquier país. |
| 2026-03-11 | Facturación electrónica: Etapa 2, fuera del MVP | Vía tercero (API proveedor autorizado DGII). Configurable por empresa. No bloquea MVP. |
| 2026-03-11 | Sistema multimoneda: 3 capas en todo documento | LC (local), SY (sistema), FC (extranjera). Ver Sección B. |
| 2026-03-11 | Valorización inventario: FIFO y Promedio Ponderado | Configurable por empresa. Solo estas dos opciones. |
| 2026-03-11 | Configuraciones bloqueadas tras primer asiento | Moneda LC, Moneda SY y Método inventario se sellan al postear el primer JE. Bloqueo técnico. |
| 2026-03-11 | Número de asiento: INT incremental por empresa | Entero autoincremental, secuencial, único por empresa. No se reinicia por período. |
| 2026-03-11 | Estados de período contable: 3 estados | Abierto / Cerrado / Abierto para ventas. Ver Sección B. |
| 2026-03-11 | Modificación de asientos en período cerrado | Permitida. El período se reabre, se modifica y debe ejecutarse el cierre nuevamente. |
| 2026-03-11 | Nómina: módulo Core del sistema | Incluida como módulo core, no complementaria. |
| 2026-03-11 | Activación de módulos SaaS: planes + custom | Planes predefinidos (Basic/Pro/Enterprise) + selección custom de módulos por cliente. |
| 2026-03-11 | MVP: primero web completo, luego Flutter mobile | App Flutter se desarrolla después del frontend web. |
| 2026-03-11 | Autenticación: JWT propio en FastAPI | Módulo auth/ con python-jose. Sin servicios externos (Auth0, Supabase Auth, Clerk, etc.). |
| 2026-03-11 | Repositorio GitHub: SIMUTECHRINKOS/rinkos_erp | https://github.com/SIMUTECHRINKOS/rinkos_erp.git |

---

## 10. PREGUNTAS PENDIENTES DE RESPUESTA

Las siguientes decisiones de negocio NO han sido definidas aún.
NO implementar nada relacionado hasta tener respuesta:

- [x] ~~¿Países de lanzamiento inicial?~~ → RD (DGII). Sistema 100% configurable para cualquier país.
- [x] ~~¿Método de valorización de inventario?~~ → FIFO y Promedio Ponderado, configurable por empresa. Ver Sección B.2.
- [ ] ¿Cuál es la estructura de roles y permisos específica de RINKOS ERP? (definir en Fase 1B)
- [x] ~~¿Facturación electrónica en MVP?~~ → Etapa 2, vía tercero (API proveedor DGII), configurable.
- [x] ~~¿Cómo se forma el número de asiento?~~ → INT incremental por empresa. Ver Sección B.3.
- [x] ~~¿Asientos en período cerrado?~~ → Permitido reabriendo el período. Ver Sección B.4.
- [x] ~~¿La nómina es core o complementaria?~~ → Core del sistema.
- [x] ~~Carta gráfica y paleta de colores~~ → Completada. Ver Sección A.
- [x] ~~¿Moneda base del sistema?~~ → Multimoneda: LC + SY + FC. Ver Sección B.1.
- [x] ~~¿Cómo se activan los módulos SaaS?~~ → Planes predefinidos (Basic/Pro/Enterprise) + selección custom.
- [x] ~~¿MVP incluye Flutter desde el inicio?~~ → No. Primero web completo, luego Flutter.
- [ ] Reglas de bloqueo adicionales por módulo (se definen módulo a módulo durante el desarrollo)
- [ ] Estructura de roles y permisos de RINKOS ERP (definir en Fase 1B)

---

## 11. CÓMO USAR ESTE DOCUMENTO EN CLAUDE CODE

### Al iniciar cada sesión de trabajo:
```
1. Abrir este archivo: docs/CLAUDE_CONTEXT.md
2. En Claude Code escribir:
   "@docs/CLAUDE_CONTEXT.md Lee este contexto completo antes de empezar."
3. Indicar la fase y módulo específico de la sesión.
4. Trabajar en un solo módulo / capa por sesión.
```

### Al cerrar cada sesión de trabajo:
```
1. Actualizar Sección 9 (Decisiones Técnicas) con lo resuelto hoy.
2. Actualizar Sección 10 (Preguntas Pendientes) — agregar o tachar.
3. Actualizar Sección 8 (estado de la fase trabajada).
4. Hacer commit: git commit -m "docs: actualizar CLAUDE_CONTEXT sesión [fecha]"
```

### Tipos de sesión recomendados (un alcance por sesión):
```
- "Sesión DB":      Solo modelo de datos + migración Alembic
- "Sesión API":     Solo endpoints FastAPI de un módulo
- "Sesión UI Web":  Solo pantallas React de un módulo
- "Sesión Mobile":  Solo pantallas Flutter de un módulo
- "Sesión QA":      Solo tests de un módulo
- "Sesión Revisión contable": Validar asientos de un módulo
```

---

*Versión: 1.5 | Fecha: 2026-03-11 | Proyecto: RINKOS ERP*
*Este documento es la autoridad máxima del proyecto. Actualizar en cada sesión.*
