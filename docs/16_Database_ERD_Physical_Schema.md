# Volume 16 — Database ERD & Physical Schema

PostgreSQL 16 physical schema for Ceragem CIOS. Logical spec names map to implemented tables via `backend/app/schema/registry.py`.

## Logical → Physical Mapping

| Spec Table | Physical Table | Notes |
|------------|----------------|-------|
| customer | customers | `email_address` → `email`, `zip_code` → `zip` |
| customer_intelligence | customer_intelligence | `intelligence_id` → `id` |
| upload_file | raw_upload | Immutable raw upload metadata |
| upload_history | upload_history | Trigger on upload complete |
| campaign | campaign | `campaign_status` → `status` |
| campaign_target | campaign_target | Audience linkage |
| campaign_report | campaign_report | Normalized import summary |
| campaign_learning | campaign_learning | Learning records |
| recommendation | recommendation | Synced from intelligence |
| provider | provider | Provider master |
| provider_mapping | provider_field_mapping | Export/import field map |
| user_account | users | Email PK |
| role | role | Reference roles |
| permission | permission | Module permissions |
| audit_log | audit_log | Immutable audit trail |
| export_history | export_job | Export jobs |

## ERD (Section 4)

```
customers ──1:1── customer_intelligence ──► recommendation
     │                    │
     │                    └── campaign_target ──► campaign
     │                                              │
     └── upload_history ◄── raw_upload           ├── campaign_report
                                                    └── campaign_learning

provider ──► provider_field_mapping
role / permission (reference)    users ──► audit_log
```

## Indexes (Section 8)

Applied on startup via `apply_physical_schema()` — see `backend/app/schema/views.py` (`INDEX_DDL`).

High priority: email, state, zip, campaign status/type, ceragem_segment, purchase_power, campaign_priority, recommended_product.

Composite: `(state, zip)`, `(status, provider)`, `(ceragem_segment, purchase_power_index)`, `(campaign_id, customer_id)`.

## Views (Section 10)

| View | Purpose |
|------|---------|
| vw_customer_summary | Dashboard customer summary |
| vw_campaign_summary | Campaign dashboard |
| vw_state_summary | State dashboard |
| vw_zip_summary | ZIP dashboard |
| vw_product_summary | Product dashboard |
| vw_roi_summary | ROI dashboard |

## Materialized Views (Section 11)

| MV | Purpose | Refresh |
|----|---------|---------|
| mv_campaign_forecast | Forecast dashboard | On report import (PostgreSQL) |
| mv_state_revenue | State revenue | Scheduled |
| mv_product_performance | Product dashboard | Scheduled |

## Triggers (Section 12)

Implemented cross-database in `backend/app/schema/triggers.py`:

| Trigger | Action |
|---------|--------|
| Customer Upload | Create `upload_history` |
| Intelligence Generated | Set `generated_at`, sync `recommendation` |
| Campaign Completed | Update `actual_revenue` on import |
| Campaign Report Imported | Refresh materialized views |

## PostgreSQL DDL

```bash
psql $DATABASE_URL -f backend/db/postgresql/16_physical_schema.sql
```

## Maintenance (Section 13)

Daily: backup, ANALYZE. Weekly: VACUUM ANALYZE. Monthly: REINDEX. Quarterly: statistics review.

## Run Tests

```bash
cd backend && python tests/test_volume16_acceptance.py
cd backend && python tests/run_acceptance.py
```
