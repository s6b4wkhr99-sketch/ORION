# Volume 17 — Analytics, Reporting & Executive Intelligence

Version 1.0 — Approved specification implemented in CIOS.

## Purpose

Transform campaign execution data into strategic business insights for executives, marketing leadership, and BI teams.

## Architecture

```
Customer Intelligence → Campaign Performance → Provider Reports → Learning Database
  → Analytics Engine → Executive Dashboard → Business Insight → Strategic Recommendation
```

## Backend Implementation

| Component | Path |
|-----------|------|
| Executive intelligence (6 areas) | `backend/app/analytics/executive.py` |
| Business insight engine | `backend/app/analytics/insights.py` |
| Executive recommendation engine | `backend/app/analytics/recommendations.py` |
| Comparative analysis | `backend/app/analytics/comparative.py` |
| Trend analysis | `backend/app/analytics/trends.py` |
| Learning intelligence | `backend/app/analytics/learning_intel.py` |
| Executive scorecard | `backend/app/analytics/scorecard.py` |
| Executive alerts | `backend/app/analytics/alerts.py` |
| Report generation | `backend/app/analytics/reports.py` |
| KPI library | `backend/app/analytics/kpi.py` |
| Report storage model | `backend/app/models/analytics.py` |

## API Endpoints (`/api/v1`)

| Endpoint | Section | Purpose |
|----------|---------|---------|
| `GET /analytics/executive` | 3–11 | Unified executive dashboard (6 intelligence areas) |
| `GET /analytics/insights` | 14 | Auto-generated business insights |
| `GET /analytics/recommendations` | 15 | Strategic next actions |
| `GET /analytics/compare` | 16 | Campaign/state/ZIP/product/segment/provider comparison |
| `GET /analytics/trends` | 17 | Revenue, customer, campaign, ROI, learning trends |
| `GET /analytics/learning` | 12 | Learning score, forecast accuracy, campaign learning |
| `GET /analytics/scorecard` | 25 | Platform health dimensions + overall business score |
| `GET /analytics/alerts` | 24 | Threshold-based executive alerts |
| `POST /analytics/reports/generate` | 18–19 | Generate daily/weekly/monthly/quarterly/annual reports |
| `GET /analytics/reports` | 18 | List generated reports |
| `GET /analytics/reports/{id}` | 18 | Report metadata |
| `GET /analytics/export` | 23 | CSV export of executive KPIs |

All endpoints use the standard envelope, `require_dashboard` RBAC, and global filter query params (`upload_id`, `state`, `zip`, `product`, `provider`, `campaign_type`, `segment`, `campaign_id`).

## Executive KPI Library (Section 20)

KPIs include rule traceability via `DASHBOARD_RULE_MAP` (`backend/app/rules/library.py`):

- Revenue, Campaign ROI, Campaign Success Rate, Forecast Accuracy
- Customer Growth, Average Order Value, Campaign Conversion
- Learning Score, Le Frame Incentive

## Drill-down (Section 21)

The executive payload includes `drill_down` navigation paths to state, ZIP, campaign, and customer APIs.

## Chart Types (Section 13)

Supported chart types are listed in the executive response (`chart_types_supported`).

## Report Formats

MVP: CSV and JSON. Excel/PDF requests store CSV + JSON payload for downstream conversion.

## Tests

```bash
cd backend && python tests/test_volume17_acceptance.py
```

Included in full regression via `run_acceptance.py`.

## Dependencies

- Volume 04 — Intelligence Engine
- Volume 06 — Campaign Operating System / Learning
- Volume 05/08 — Dashboard APIs and UX
- Volume 16 — Physical schema (`campaign_learning`, views)
