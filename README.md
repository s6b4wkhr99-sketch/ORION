# Ceragem Customer Intelligence Operating System (CIOS)

**Version:** 1.1.0 · **Status:** Local Native Pilot

Customer Intelligence Operating System for Ceragem and Le Frame. Implementation follows approved specifications in [`docs/`](./docs/).

**Current development status:** [Volume 31 — Development Status Report](./docs/31_Development_Status_Report.md) · [CHANGELOG](./CHANGELOG.md)

---

## 1. Project Overview

Ceragem Customer Intelligence Operating System (CIOS) is an enterprise customer intelligence platform designed to transform uploaded customer data into actionable campaign intelligence.

**CIOS is not a CRM.**

**CIOS is not a Mass Email Provider.**

CIOS is a Customer Intelligence Operating System that connects customer data, Datalogix intelligence, ZIP intelligence, PRIZM Proxy segmentation, Ceragem commercial segmentation, campaign forecasting, provider export, campaign report import, and executive analytics into one operating platform.

---

## 2. Core Objective

CIOS enables Ceragem and Le Frame to answer the following business questions:

- Which customers are most likely to purchase?
- Which State should be prioritized?
- Which ZIP has the highest opportunity?
- Which Ceragem product should be recommended?
- Which message direction should be used?
- What is the expected conversion?
- What is the expected revenue?
- What is the expected Le Frame incentive?
- Which campaign should be executed next?

---

## 3. Core Workflow

```text
Excel / CSV Upload
        ↓
Auto Mapping Engine
        ↓
Data Standardization
        ↓
Validation
        ↓
Customer Database
        ↓
Datalogix Intelligence
        ↓
ZIP Intelligence
        ↓
PRIZM Proxy Segment
        ↓
Ceragem Segment
        ↓
Message Direction
        ↓
Recommendation Engine
        ↓
Revenue Forecast
        ↓
Dashboard
        ↓
Provider Export
        ↓
Campaign Execution
        ↓
Campaign Report Import
        ↓
Learning Database
```

---

## 4. Repository Structure

```text
CIOS/
  frontend/     Next.js, React, TypeScript, Tailwind, Recharts
  backend/      FastAPI, SQLAlchemy, Pandas
  docs/         Approved specifications (Volumes 01–23)
  spec/         Pointer to docs/
  sample_data/  CSV samples for upload and campaign reports
```

---

## 5. Quick Start (Local Native)

**Full guide:** [Local Operations Quickstart](./docs/Local_Operations_Quickstart.md)

```bash
make setup-local          # first time only
make postgres-up
make migrate
bash scripts/dev.sh start # or double-click Start CIOS.command
```

Check status: `bash scripts/dev.sh status`

Default login: `user@company.com` / `Ceragem2026!Adm` (System Administrator, local dev only)

---

## 5b. Legacy manual start

```bash
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./run_backend.sh

cd frontend && npm install && ./run_frontend.sh
```

---

## 6. Documentation Library

Full specification index: [`docs/README.md`](./docs/README.md) (Volumes 01–27).

Key volumes:

| Volume | Topic |
|--------|-------|
| 04 | Intelligence Engine |
| 07 | API Specification |
| 08 | Cursor Development Guide |
| 09 | Field Mapping & Data Dictionary |
| 14 | Operations Manual |
| 21 | Master Index & Knowledge Governance |
| 22 | Reference Data Library |
| **27** | **Development Completion Specification (개발완료 개발서 — As-Built)** |
| 23 | Project README (this document) |

Knowledge Hub API: `GET /api/v1/knowledge`

---

## 7. API

Base URL: `/api/v1`

```json
{ "success": true, "data": {} }
{ "success": false, "message": "Error message" }
```

Legacy `/api/*` routes remain for backward compatibility.

---

## 8. Development Rules (Volume 08)

1. **Specification first** — implement only what is in `/docs`
2. **No new architecture** unless explicitly requested
3. **Configuration-driven** mappings and reference data (Volumes 09, 22)
4. **Preserve Datalogix** X/Y/Z/U as strings, never numeric
5. **Business logic in services** — not in route handlers
6. **Auto Mapping** — no manual field mapping in normal upload (RFC-001)

---

## 9. Tests

```bash
cd backend && source .venv/bin/activate && python tests/run_acceptance.py
```

Volume 12 QA catalog: `python tests/test_volume12_qa.py`

---

## Local development (quick start)

PostgreSQL must be reachable at `127.0.0.1:5432`. See **[Local Operations Quickstart](./docs/Local_Operations_Quickstart.md)**.

```bash
make setup-local
make postgres-up
make migrate
bash scripts/dev.sh start    # keep Terminal open
make dev-status              # diagnose issues
```

Async uploads: `make worker` (or `bash scripts/dev.sh start --with-worker`)

Health check: `curl http://127.0.0.1:8000/api/v1/health`

Login: [http://127.0.0.1:3002/login](http://127.0.0.1:3002/login)

---

## 10. Deployment & Operations

```bash
docker compose --env-file deploy/env/development.env up -d
```

Health: `GET /api/v1/health` · Admin: `/admin` · Upload: `/import`

---

## Pages

Dashboard · Customer Intelligence · Upload Center (`/import`) · Campaign Center · Campaign Performance · State / ZIP / Product Intelligence · ROI Center · Export Center · Settings
