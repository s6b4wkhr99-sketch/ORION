# Volume 02 — Platform Architecture

Version 1.0 — Approved

---

## Document Information

| Item | Value |
|------|-------|
| Document | Platform Architecture |
| Version | 1.0 |
| Status | Approved |
| Project | Ceragem Customer Intelligence Operating System (CIOS) |
| Dependency | Volume 01 — Executive Proposal |

---

## 1. Purpose

Defines the system architecture, technology stack, module boundaries, and data flow for CIOS.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│  Dashboard · Customer Intelligence · Campaign · Analytics   │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST /api/v1
┌──────────────────────────▼──────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  Acquisition · Intelligence · Campaign · Analytics · AI     │
└──────────────────────────┬──────────────────────────────────┘
                           │ SQLAlchemy
┌──────────────────────────▼──────────────────────────────────┐
│              Database (SQLite dev / PostgreSQL prod)         │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Charts / Tables | Recharts, TanStack Table |
| Backend | FastAPI, Python 3.12 |
| ORM | SQLAlchemy |
| Data Processing | Pandas |
| Auth | JWT, bcrypt, RBAC |
| Dev Database | SQLite |
| Production Database | PostgreSQL 16 |
| Containerization | Docker Compose |
| CI/CD | GitHub Actions |

---

## 4. Repository Structure

```text
CIOS/
├── frontend/          Next.js application
├── backend/           FastAPI application
│   └── app/
│       ├── acquisition/     Upload & validation
│       ├── intelligence/    Intelligence pipeline
│       ├── segmentation/    Approved intelligence entry point
│       ├── campaign/        Campaign OS
│       ├── analytics/       Executive analytics
│       ├── ai_engine/       Recommendation engine
│       ├── providers/       Provider adapters
│       ├── methodology/     Le Frame methodology (Vol 20)
│       ├── knowledge/       Master index (Vol 21)
│       ├── schema/          Physical schema (Vol 16)
│       ├── rules/           Business rule library (Vol 10)
│       ├── security/        RBAC & audit (Vol 11)
│       └── api/v1/          REST API router
├── docs/              Approved specifications (Volumes 01–21)
├── deploy/            Environment & deployment configs
└── sample_data/       CSV samples
```

---

## 5. Core Modules

| Module | Responsibility | Volume |
|--------|----------------|--------|
| Acquisition | Customer upload, validation, mapping | 06, 08, 09 |
| Intelligence Engine | Datalogix, ZIP, PRIZM, segments, forecasts | 04, 19 |
| Campaign OS | Create, forecast, export, report import | 06 |
| Provider Integration | Export/import adapters | 15 |
| AI Recommendation Engine | Product, message, campaign recommendations | 18 |
| Executive Analytics | KPIs, insights, scorecard, reports | 17 |
| Learning | Campaign learning records | 06, 18 |
| Security | Authentication, RBAC, audit | 11 |

---

## 6. Data Flow

```
Raw Upload (CSV/XLSX)
    → Field Mapping (canonical dictionary)
    → Customer Record + Datalogix preservation
    → Intelligence Pipeline
    → Customer Intelligence + Recommendation
    → Campaign Targeting
    → Provider Export
    → Campaign Report Import
    → Campaign Learning
    → Executive Analytics
```

---

## 7. API Architecture

- Base path: `/api/v1`
- Standard envelope: `{ success, data }` / `{ success, message }`
- JWT authentication with role-based permissions
- Business logic in service layer, not route handlers
- Implementation: `backend/app/api/v1/router.py`

See Volume 07 — API Specification.

---

## 8. Intelligence Architecture

Entry point: `backend/app/segmentation/` (re-exports `app.intelligence`)

Pipeline order: Normalization → Datalogix → ZIP → PRIZM → Ceragem Segment → Message Direction → Purchase Power → Pain Index → Lifestyle → Recommendation → Revenue Forecast → Calculation Framework (Vol 19)

See Volume 04 — Intelligence Engine.

---

## 9. Cross-Cutting Concerns

| Concern | Implementation |
|---------|----------------|
| Business Rules | `app.rules.library` — single source of truth |
| Field Dictionary | `app.mapping.data_dictionary` |
| Audit Logging | Immutable `audit_log` table |
| Explainability | `trace_json`, `framework_json`, AI audit |
| Version Governance | Methodology + knowledge registries |

---

## 10. Dependencies

| Volume | Document |
|--------|----------|
| 03 | Database Architecture |
| 04 | Intelligence Engine |
| 07 | API Specification |
| 08 | Cursor Development Guide |
| 16 | Database ERD & Physical Schema |
