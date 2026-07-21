# Volume 15 — Provider Integration Specification

Provider-agnostic mass email integration via the **Provider Integration Layer** (`backend/app/providers/`).

## Architecture (Section 3)

Intelligence and campaign engines never import provider-specific code. All provider differences live in:

- `providers/config.py` — field and metric mappings
- `providers/adapter.py` — adapter implementations (mapping only)
- `export_template` table — seeded export column labels

## Supported Providers (Section 4)

Generic CSV, Klaviyo, Mailchimp, HubSpot, Attentive, Salesforce Marketing Cloud

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/providers` | List providers + mapping versions |
| `GET /api/v1/providers/{name}` | Provider export/import specification |
| `POST /api/v1/export` | Provider export with validation |
| `POST /api/v1/report/upload` | Provider report import with detection |

## Adapter Interface (Section 7)

Each adapter implements: `generate_export`, `validate_export`, `build_import_column_map`, `normalize_metrics`, `validate_import`, `generate_audit_log`.

## Internal Metrics (Section 16)

Provider columns normalize to: `total_sent`, `delivered`, `opened`, `unique_open`, `clicked`, `unique_click`, `actual_revenue`, `actual_orders`, `bounce`, `unsubscribe`.

## Adding a Provider (Section 20)

1. Add name to `providers/constants.py`
2. Add export extensions + import metrics in `providers/config.py`
3. Seed `export_template` rows
4. Register adapter class (automatic via `ADAPTER_CLASSES`)

No changes required to Intelligence Engine, Campaign Engine, Dashboard, or Learning modules.

## Run Tests

```bash
cd backend && python tests/test_volume15_acceptance.py
cd backend && python tests/run_acceptance.py
```
