# Volume 19 — Intelligence Calculation Framework

Version 1.0 — Approved specification implemented in CIOS.

## Purpose

Defines **how** intelligence is calculated: deterministic, explainable, repeatable, version-controlled, and business-rule driven.

## Pipeline Integration

After Volume 04 engines complete, `apply_calculation_framework()` runs as the final pipeline step:

```
Normalization → Datalogix → ZIP → PRIZM → Ceragem → Message → PP → Pain → Lifestyle → Recommendation → Forecast → **Framework**
```

Implementation: `backend/app/intelligence/calculation_framework.py`, invoked from `pipeline.py`.

## Intelligence Categories (Section 3)

| Category | Framework output |
|----------|------------------|
| purchase_power | score 0–100, High/Medium/Low, confidence, explanation |
| pain_index | score, level, confidence, explanation |
| lifestyle | score, level, confidence, explanation |
| prizm_proxy | segment, score, confidence, explanation |
| ceragem_segment | V19 commercial label + V04 segment, score, confidence |
| recommendation | product/campaign/message, score, confidence |
| revenue | expected revenue, range, confidence |
| conversion | expected conversion/orders, confidence |
| campaign_priority | grade A–D, score, confidence |

## Score Normalization (Section 17)

All framework scores use `normalize_score()` — clamped **0–100**.

## Confidence (Section 13)

Per-category confidence 0–100 with categories: Very High, High, Medium, Low, Unknown (reuses `app/ai_engine/confidence.py`).

## Explainability (Section 16)

Each category includes:

- `primary_factors`
- `secondary_factors`
- `supporting_rules`
- `confidence` + `confidence_category`
- `calculation_version`
- `business_rule_id`

## Versioning (Section 14)

Stored on `CustomerIntelligence`:

- `rule_version`
- `calculation_version` (`Volume 19 v1.0`)
- `engine_version`
- `generated_by`
- `framework_json` (full framework payload + audit)

## Audit (Section 18)

Each calculation records `calculation_id`, execution time, confidence summary, and errors in `framework.audit`.

## Recalculation (Section 15)

Allowed on: rule version change, reference data change, customer upload, administrator regeneration. Historical campaign learning records remain immutable.

## API

| Endpoint | Purpose |
|----------|---------|
| `GET /intelligence/framework/{customer_id}` | Full calculation framework |
| `GET /intelligence/customer/{customer_id}` | Customer intelligence + framework summary |

## Rule Traceability

`CALCULATION_FRAMEWORK_MAP` in `backend/app/rules/library.py` maps categories to business rule IDs.

## Tests

```bash
cd backend && python tests/test_volume19_acceptance.py
```

## Dependencies

- Volume 04 — Intelligence Engine (rule execution)
- Volume 10 — Business Rule Library
- Volume 18 — AI Recommendation Engine (consumes intelligence scores)
