# Volume 18 — AI Intelligence & Recommendation Engine

Version 1.0 — Approved specification implemented in CIOS.

## Purpose

Transform Customer Intelligence into executable, explainable marketing recommendations by combining deterministic Business Rules with campaign learning.

## Design Philosophy

1. **Rule First** — Business Rules 065–067 execute first (`app/intelligence/recommendation_rules.py`)
2. **Learning Second** — `CampaignLearning` and `LearningCampaign` adjust confidence (`app/ai_engine/learning.py`)
3. **AI Third** — Engine ranks valid rule outputs; never overrides mandatory rules

## Architecture

```
Customer → Intelligence Pipeline → Business Rules → Campaign Learning → AI Engine → recommendation table
```

## Backend Implementation

| Module | Path |
|--------|------|
| Orchestrator | `backend/app/ai_engine/engine.py` |
| Confidence scoring | `backend/app/ai_engine/confidence.py` |
| Learning weights | `backend/app/ai_engine/learning.py` |
| Constants | `backend/app/ai_engine/constants.py` |
| API services | `backend/app/api/services/ai_recommendation.py` |
| Layer alias | `backend/app/learning/recommendation.py` |

## Recommendation Database (Section 18)

Table `recommendation` stores product, message, campaign, confidence, reason, rule/learning/engine versions, ranking JSON, scores JSON, and audit JSON.

Populated on customer upload via `sync_recommendation_from_intelligence()` → `run_ai_recommendation_for_intelligence()`.

## API Endpoints (`/api/v1`)

| Endpoint | Section |
|----------|---------|
| `GET /intelligence/recommendation/{customer_id}` | Full recommendation payload |
| `GET /intelligence/recommendation/{customer_id}/product` | Product engine |
| `GET /intelligence/recommendation/{customer_id}/message` | Message engine |
| `GET /intelligence/recommendation/{customer_id}/campaign` | Campaign engine |
| `GET /intelligence/recommendation/{customer_id}/geographic` | Geographic engine |
| `GET /intelligence/prediction/revenue/{customer_id}` | Revenue prediction |
| `GET /intelligence/prediction/conversion/{customer_id}` | Conversion prediction |

Backward-compatible fields on full recommendation: `recommendedProduct`, `messageDirection`, `campaignPriority`, `expectedRevenue`, `expectedConversion`.

## Scores (Section 19–21)

Each recommendation includes 0–100 scores: customer, revenue, conversion, campaign, recommendation, priority, learning.

Business priority grades **A–D** and campaign readiness **Ready / Review / Hold**.

## Rule Traceability

`AI_RULE_MAP` in `backend/app/rules/library.py` links engine outputs to business rule IDs.

## Tests

```bash
cd backend && python tests/test_volume18_acceptance.py
```

## Dependencies

- Volume 04 — Intelligence Engine & Rules 065–067
- Volume 06 — Campaign Learning
- Volume 10 — Business Rule Library
- Volume 16 — `recommendation` table
- Volume 17 — Executive analytics (separate strategic layer)
