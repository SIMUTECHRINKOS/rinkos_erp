# RINKOS ERP

Plataforma ERP SaaS multidispositivo para PYMES latinoamericanas.

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | FastAPI (Python 3.12+) |
| Base de Datos | PostgreSQL 16+ (Supabase) |
| ORM | SQLAlchemy 2.0 + Alembic |
| Frontend Web | React 18 + Vite + Ant Design Pro |
| Mobile | Flutter 3.x |
| Cache / Queue | Redis |
| Hosting Backend | Railway.app |
| Hosting Frontend | Vercel |

## Estructura del Monorepo

```
rinkos-erp/
├── backend/          # FastAPI
├── frontend/         # React + Vite
├── mobile/           # Flutter
├── docs/             # Documentación y contexto
├── infra/            # Scripts de infraestructura
├── CONVENTIONS.md    # Convenciones de código obligatorias
└── README.md
```

## Inicio Rápido

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Configurar variables de entorno
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

### Mobile
```bash
cd mobile
flutter pub get
flutter run
```

## Documentación

- **Contexto del proyecto**: `docs/CLAUDE_CONTEXT.md`
- **Convenciones de código**: `CONVENTIONS.md`
- **ERD**: `docs/ERD/`
- **Especificaciones de módulos**: `docs/modules/`

## Principio Rector

> La contabilidad es la columna vertebral de RINKOS ERP.
> Toda transacción operativa genera asientos contables automáticos.
> Si la contabilidad no puede registrar el evento, el evento no ocurre.

---

*Versión: 0.1.0 | Estado: Fase 0 — Fundación*
