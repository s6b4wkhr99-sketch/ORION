# RFC-001 — Customer Upload Auto Mapping Engine Revision

**Version:** 1.1  
**Status:** Approved  
**Priority:** Critical

## Summary

Replaces manual Mapping Preview with an automatic mapping pipeline. Customer uploads no longer require user field mapping during normal operation.

## New Workflow

```
Customer Upload → Header Detection → Alias Dictionary Lookup → Auto Mapping Engine
→ Data Standardization → Validation → Normalization → Import → Intelligence → Dashboard
```

## Components (implemented)

| Component | Module |
|-----------|--------|
| Header Detection Engine | `app/mapping/auto_engine.py` |
| Alias Dictionary | `field_alias` table + `GET /api/v1/mapping/aliases` |
| Auto Mapping Engine | `app/mapping/auto_engine.py` |
| Confidence Engine | Match-type confidence scores in mapping report |
| Data Standardization | `app/mapping/standardization.py` |
| Validation Engine | `validate_mapping()` + `POST /api/v1/mapping/validate` |
| Mapping Report | `POST /api/v1/mapping/report` + Upload preview response |
| Unknown Header Resolver | Logged to `mapping_exception`; upload not blocked |

## Database Tables

- `field_master` — canonical internal fields
- `field_alias` — header aliases (administrator-approved aliases stored here)
- `provider_template` — provider-specific upload templates
- `mapping_history` — per-upload mapping audit trail
- `mapping_exception` — unresolved / review headers

## API Endpoints

- `GET /api/v1/mapping/fields`
- `GET /api/v1/mapping/aliases`
- `POST /api/v1/mapping/validate`
- `POST /api/v1/mapping/report`
- `POST /api/v1/mapping/standardize`

## UI

- `/import` — Mapping Report (read-only) replaces Mapping Preview
- Upload Center steps: Detected Headers → Auto Mapping → Mapping Report → Validation → Import

## Match Priority

1. Exact Match (100%)
2. Alias Match (95–99%)
3. Provider Template (90–95%)
4. AI Similarity Match (80–90%)
5. Unknown Field (&lt;80% — logged, does not block upload)

## Acceptance Tests

Run: `python tests/test_rfc001_acceptance.py`

## Volumes Updated

- Volume 05 — Mapping Report UI
- Volume 08 — Upload workflow
- Volume 09 — Alias dictionary + confidence
- Volume 14 — Upload operation
- Volume 16 — Mapping tables
