# Volume 09 — Field Mapping & Data Dictionary

Single Source of Truth for all CIOS field definitions.

## Implementation

Canonical definitions: `backend/app/mapping/data_dictionary.py`

| Module | Usage |
|--------|--------|
| Upload mapping | `UPLOAD_SOURCE_MAPPINGS` → `field_mapping` table |
| Export | `EXPORT_PROVIDER_MAPPINGS` → `export_template` table |
| Campaign reports | `CAMPAIGN_REPORT_ALIASES` |
| Validation | `REQUIRED_UPLOAD_FIELDS`, Section 21 rules in `processing/validator.py` |
| Dashboard | `DASHBOARD_METRIC_MAP` |

## Naming Convention (Section 3)

Internal fields use `snake_case`: `email_address`, `zip_code`, `purchase_power`, etc.

## Database Compatibility (Section 23)

Legacy DB columns map via `INTERNAL_TO_DB`:

- `email_address` → `email`
- `zip_code` → `zip`
- `net_worth_indicator` → `net_worth`
- `total_sent` → `sent` (campaign performance)
- `actual_revenue` → `revenue`

## Field Categories

Customer, Geographic, Datalogix, Intelligence, Campaign, Forecast, Provider, Performance, Learning, ZIP Intelligence — all registered in `FIELD_REGISTRY`.

## Datalogix Preservation (Section 7)

Original Datalogix values are never modified before storage. X/Y/Z/U remain strings.

## Tests

```bash
cd backend && python tests/test_volume09_acceptance.py
```
