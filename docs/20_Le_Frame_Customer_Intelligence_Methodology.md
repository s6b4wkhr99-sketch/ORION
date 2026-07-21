# Volume 20 — Le Frame Customer Intelligence Methodology

Version 1.0 — Approved specification. CIOS is the operational implementation of this methodology.

## Purpose

Defines the proprietary Le Frame Customer Intelligence Methodology for high-consideration consumer products. Customer Intelligence — not email delivery — is the strategic objective.

## Philosophy

> Customers purchase when the right product, the right message and the right timing meet the right customer.

## Implementation

| Component | Path |
|-----------|------|
| Methodology registry | `backend/app/methodology/registry.py` |
| Service layer | `backend/app/methodology/service.py` |

## Customer Intelligence Pyramid (Section 3)

Seven levels from Raw Customer Data through Executive Intelligence, each increasing business value.

## Seven Intelligence Layers (Section 4)

| Layer | CIOS Module |
|-------|-------------|
| 1 Raw Customer Data | `app.acquisition.upload` |
| 2 Geographic Intelligence | `app.intelligence.zip_engine` |
| 3 Behavioral Intelligence | `app.intelligence.datalogix_engine` |
| 4 Commercial Intelligence | `app.intelligence.calculation_framework` |
| 5 Campaign Intelligence | `app.campaign.analytics` |
| 6 Executive Intelligence | `app.analytics.executive` |
| 7 Continuous Learning | `app.learning.campaign_learning` |

## Decision Model (Section 12)

```
Customer → Intelligence → Recommendation → Campaign → Learning → Intelligence
```

## Methodology Areas

- **Geographic Intelligence** (Section 5) — ZIP/State opportunity, not just address
- **Datalogix** (Section 6) — categorical preservation via `preserve_datalogix_value()`
- **PRIZM Proxy** (Section 7) — internal lifestyle framework
- **Ceragem Segments** (Section 8) — proprietary commercial segments (V19 mapping)
- **Purchase Power / Pain / Lifestyle** (Sections 9–11) — Volume 04 + Volume 19 framework
- **Recommendations** (Section 13) — Volume 18 AI engine (Rule First → Learning → AI)
- **Campaign Intelligence** (Section 14) — Volume 06 + Volume 15
- **Email Conversion** (Section 15) — nine-stage funnel model
- **Forecast** (Section 16) — deterministic Volume 06 rules
- **Executive Decisions** (Section 17) — Volume 17 analytics
- **Learning** (Section 18) — immutable records, future weight adjustment
- **Explainability** (Section 19) — mandatory across framework + AI engine

## API Endpoints (`/api/v1`)

| Endpoint | Section |
|----------|---------|
| `GET /methodology` | Full methodology overview + implementation status |
| `GET /methodology/pyramid` | Intelligence pyramid |
| `GET /methodology/layers` | Seven intelligence layers |
| `GET /methodology/governance` | Governance requirements + success criteria |
| `GET /methodology/success-criteria` | Runtime success criteria verification |

## Governance (Section 23)

Updates require: Business Validation, Rule Review, Executive Approval, Documentation Update, Regression Testing.

Verified via `python tests/run_acceptance.py`.

## Success Criteria (Section 24)

Eight criteria mapped to implemented modules and APIs — verified in `test_volume20_acceptance.py`.

## Dependencies

All prior volumes (04–19) plus platform architecture.

## Tests

```bash
cd backend && python tests/test_volume20_acceptance.py
```
