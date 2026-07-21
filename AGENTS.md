# Ceragem CIOS — Agent Instructions

Before making changes, read the approved specifications in [`docs/`](./docs/).

Follow [Volume 08 Cursor Development Guide](./docs/08_Cursor_Development_Guide.md):

- Specification first — do not redesign or add features
- Business logic in services, schemas in `backend/app/schemas/`
- Intelligence via `backend/app/segmentation/`
- Standard API envelope and audit logging

Run acceptance tests: `cd backend && python tests/run_acceptance.py`

Field dictionary (Volume 09): `backend/app/mapping/data_dictionary.py` — canonical internal field names for upload, export, campaign reports, and dashboards.

Business rules (Volume 10): `backend/app/rules/library.py` — authoritative Rule IDs; intelligence traces include `business_rule_id` for explainability.

Security & RBAC (Volume 11): `backend/app/security/` — roles, permissions, bcrypt passwords, immutable audit logs. JWT role is enforced when a Bearer token is present.

Testing & QA (Volume 12): `backend/tests/qa_catalog.py` + `python tests/run_acceptance.py` for full regression.

Deployment & DevOps (Volume 13): `docker-compose.yml`, `deploy/env/`, `GET /api/v1/health`, Alembic migrations, `.github/workflows/cios-ci.yml`.

System Administration (Volume 14): `GET /api/v1/admin/*`, `/admin` dashboard, user administration APIs, operational checklists — `docs/14_System_Administration_Operations_Manual.md`.

Provider Integration (Volume 15): `backend/app/providers/` adapter layer, `GET /api/v1/providers`, export/import validation — `docs/15_Provider_Integration_Specification.md`.

Database ERD & Physical Schema (Volume 16): `backend/app/schema/registry.py`, views, indexes, `docs/16_Database_ERD_Physical_Schema.md`.

Analytics & Executive Intelligence (Volume 17): `backend/app/analytics/`, `GET /api/v1/analytics/*`, `docs/17_Analytics_Executive_Intelligence.md`.

AI Intelligence & Recommendation Engine (Volume 18): `backend/app/ai_engine/`, `GET /api/v1/intelligence/recommendation/*`, `docs/18_AI_Intelligence_Recommendation_Engine.md`.

Intelligence Calculation Framework (Volume 19): `backend/app/intelligence/calculation_framework.py`, `GET /api/v1/intelligence/framework/*`, `docs/19_Intelligence_Calculation_Framework.md`.

Le Frame Customer Intelligence Methodology (Volume 20): `backend/app/methodology/`, `GET /api/v1/methodology/*`, `docs/20_Le_Frame_Customer_Intelligence_Methodology.md`.

Master Index & Knowledge Governance (Volume 21): `backend/app/knowledge/`, `GET /api/v1/knowledge/*`, `docs/21_Master_Index_Cross_Reference_Knowledge_Governance.md`.

Development Convention (Volume 24): `backend/app/conventions/`, `GET /api/v1/conventions`, `docs/24_Development_Convention.md` — naming, API envelope, logging, prohibited practices.

Git Workflow & Release Management (Volume 25): `backend/app/git_workflow/`, `GET /api/v1/git-workflow`, `CHANGELOG.md`, `docs/25_Git_Workflow_Release_Management.md` — GitFlow branches, squash merge, semver, CI/CD, release tags.

CIOS Design Principles (Volume 26): `backend/app/design_principles/`, `GET /api/v1/design-principles`, `docs/26_CIOS_Design_Principles.md` — project constitution; all 23 immutable principles govern every module.
