# Volume 22 — Reference Data Library (RDL)

**Version:** 1.0  
**Status:** Final

## Purpose

The Reference Data Library (RDL) defines all standardized master reference data used throughout CIOS. Unlike customer transactional data, reference data is centrally managed, version controlled, and shared across every module.

## Design Principles

- Centralized
- Version controlled (`reference_data_version` table)
- Read-only during normal operation
- Shared by every module
- Independently maintainable

## Architecture Domains

| Domain | Tables |
|--------|--------|
| Geographic | `state_master`, `county_master`, `zip_master`, `time_zone_master`, `country_master` |
| Customer | `gender_master`, `generation_master`, `household_master`, `dwelling_master`, `income_range_master` |
| Product | `product_master` |
| Campaign | `campaign_type_master`, `campaign_status_master`, `message_type_master`, `holiday_master` |
| Intelligence | `purchase_power_master`, `pain_index_master`, `lifestyle_master`, `ceragem_segment_master`, `priority_master`, `prizm_segment_master` |
| Provider | `provider_version_master`, `provider_status_master` (+ v16 `provider`) |
| Dashboard | `dashboard_master`, `metric_master`, `chart_type_master` |
| System | `language_master`, `currency_master`, `status_master` (+ v16 `role`, `permission`) |

## Implementation

| Component | Path |
|-----------|------|
| Registry (seed SSOT) | `backend/app/reference/registry.py` |
| Models | `backend/app/models/reference_data.py` |
| Seed | `backend/app/reference/seed.py` |
| Service | `backend/app/reference/service.py` |
| Resolver | `backend/app/reference/resolver.py` |

## API Endpoints

- `GET /api/v1/reference` — catalog and counts
- `GET /api/v1/reference/products` — product catalog and MSRP
- `GET /api/v1/reference/segments` — Ceragem, PRIZM, purchase power levels
- `GET /api/v1/reference/geographic` — state/ZIP summary
- `GET /api/v1/reference/providers` — supported ESP providers
- `GET /api/v1/reference/dashboards` — dashboard and metric metadata
- `GET /api/v1/settings/reference` — RDL version

## Governance

Every reference table includes: `reference_version`, `created_date`, `modified_date`, `owner`, `approval_status`.

Changes require business review, architecture review, approval, version increment, and documentation update.

## Acceptance Tests

```bash
cd backend && python tests/test_volume22_acceptance.py
```

## Product Catalog (seeded)

Master V9, Master V7, Master V6, Master V4, Pause M6, Pause M2, MediSpa / Cellunic — new products are added via `product_master` only.
