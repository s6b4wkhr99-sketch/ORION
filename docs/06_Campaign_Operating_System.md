# Volume 06 — Campaign Operating System

Version 1.0 — Approved specification implemented in CIOS.

## Purpose

Defines campaign lifecycle management: creation, audience selection, forecast, export, report import, and learning integration.

## Backend Implementation

| Component | Path |
|-----------|------|
| Campaign CRUD | `backend/app/campaign/detail.py`, `backend/app/api/services/campaigns.py` |
| Campaign forecast | `backend/app/campaign/forecast.py` |
| Campaign export | `backend/app/campaign/export.py` |
| Campaign reports | `backend/app/campaign/reports.py` |
| Campaign dashboards | `backend/app/campaign/dashboards.py`, `backend/app/campaign/analytics.py` |
| Campaign learning | `backend/app/learning/campaign_learning.py` |
| Campaign models | `backend/app/models/campaign.py` |

## API Endpoints (`/api/v1`)

| Endpoint | Purpose |
|----------|---------|
| `GET /campaign` | List campaigns |
| `GET /campaign/{id}` | Campaign detail |
| `POST /campaign` | Create campaign |
| `PUT /campaign/{id}` | Update campaign |
| `DELETE /campaign/{id}` | Delete campaign |
| `GET /campaign/{id}/audience` | Campaign audience |
| `GET /campaign/{id}/forecast` | Campaign forecast |
| `POST /campaign/{id}/approve` | Approve campaign |
| `POST /export` | Export campaign audience |
| `POST /report/upload` | Import provider campaign report |
| `GET /report/{campaign_id}` | Campaign report data |
| `GET /learning/insights` | Campaign learning insights |

## Dependencies

- Volume 04 — Intelligence Engine
- Volume 10 — Business Rule Library (Campaign, Forecast, Learning rules)
- Volume 15 — Provider Integration (export/import)
- Volume 16 — Physical Database (`campaign`, `campaign_target`, `campaign_report`, `campaign_learning`)

## Tests

`backend/tests/test_campaign_volume06.py`
