# Ceragem Customer Intelligence Operating System (CIOS)

**Version:** 1.0 · **Status:** Final

Customer Intelligence Operating System for Ceragem and Le Frame. Implementation follows approved specifications in [`docs/`](./docs/).

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

## 5. Quick Start

```bash
# Backend (port 8000)
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./run_backend.sh

# Frontend (port 3002)
cd frontend && npm install && ./run_frontend.sh
```

Default login: `user@company.com` / `Ceragem2026!Adm` (System Administrator)

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

PostgreSQL must be reachable at `127.0.0.1:5432` (Docker or Homebrew). Credentials match `backend/.env`.

**One command** (Postgres + migrate + backend + frontend):

```bash
bash scripts/dev_local.sh
```

**Or step by step:**

```bash
make postgres-up          # Docker PostgreSQL (optional if already running)
make migrate
make backend              # http://127.0.0.1:8000
make frontend             # http://localhost:3002
```

Frontend API base URL: `frontend/.env.local` → `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`

Health check: `curl http://127.0.0.1:8000/api/v1/health`

Market Intelligence: [http://localhost:3002/market-intelligence](http://localhost:3002/market-intelligence)

---

## 10. Deployment & Operations

```bash
docker compose --env-file deploy/env/development.env up -d
```

Health: `GET /api/v1/health` · Admin: `/admin` · Upload: `/import`

---

## Pages

Dashboard · Customer Intelligence · Upload Center (`/import`) · Campaign Center · Campaign Performance · State / ZIP / Product Intelligence · ROI Center · Export Center · Settings
