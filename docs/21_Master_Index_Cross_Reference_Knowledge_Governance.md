# Volume 21 — Master Index, Cross Reference & Knowledge Governance

Version 1.0 — Approved specification. Documentation hub for the entire CIOS platform.

## Purpose

Ensures every document, database object, API, business rule, workflow, dashboard and intelligence model can be traced from a single location.

## Implementation

| Component | Path |
|-----------|------|
| Knowledge registry | `backend/app/knowledge/registry.py` |
| Service layer | `backend/app/knowledge/service.py` |

## Master Navigation (Section 3)

```
Executive → Customer Intelligence → Campaign → Forecast → Export
→ Campaign Report → Learning → Executive Analytics → Recommendation
→ Continuous Improvement
```

## Cross References

| Section | Registry Key | Runtime Source |
|---------|--------------|----------------|
| Database (§5) | `DATABASE_CROSS_REFERENCE` | `app.schema.registry.TABLE_MAP` |
| Intelligence (§6) | `INTELLIGENCE_CROSS_REFERENCE` | Intelligence + AI engine modules |
| Business Rules (§7) | `BUSINESS_RULE_CROSS_REFERENCE` | `app.rules.library.RULES` |
| Dashboards (§8) | `DASHBOARD_CROSS_REFERENCE` | Dashboard + analytics APIs |
| APIs (§9) | `API_CROSS_REFERENCE` | `app.api.v1.router` |
| Workflows (§10) | `WORKFLOW_CROSS_REFERENCE` | Upload → learning pipeline |
| Components (§11) | `COMPONENT_LIBRARY` | Volume 05 UX spec |
| Providers (§12) | `PROVIDER_INDEX` | `app.providers.adapter.ADAPTER_CLASSES` |
| Data Sources (§13) | `DATA_SOURCE_INDEX` | Volumes 03, 09, 16 |
| Executive KPIs (§14) | `EXECUTIVE_KPI_INDEX` | Volume 17 analytics |

## API Endpoints (`/api/v1`)

| Endpoint | Section |
|----------|---------|
| `GET /knowledge` | Full documentation hub overview |
| `GET /knowledge/index` | Document volumes and dependency map |
| `GET /knowledge/cross-reference` | Database, intelligence, rules, dashboards, APIs, workflows |
| `GET /knowledge/governance` | Version and documentation governance |
| `GET /knowledge/glossary` | Section 15 glossary terms |
| `GET /knowledge/acceptance-criteria` | Section 18 runtime verification |

## Version Governance (Section 16)

Every document must include: Version, Status, Owner, Created Date, Modified Date, Approval, Change Log, Cross Reference.

## Documentation Governance (Section 17)

Changes require: Business Review, Technical Review, Architecture Review, Approval, Version Increment, Publication.

## Master Acceptance Criteria (Section 18)

| ID | Criterion |
|----|-----------|
| AC-01 | Every document is indexed |
| AC-02 | Every business rule is traceable |
| AC-03 | Every database object is referenced |
| AC-04 | Every API endpoint is documented |
| AC-05 | Every workflow is indexed |
| AC-06 | Every dashboard is linked to its specification |
| AC-07 | Every intelligence model has a source document |
| AC-08 | Every methodology references its implementation |
| AC-09 | Documentation remains internally consistent |

Verified at runtime via `GET /api/v1/knowledge/acceptance-criteria`.

## Dependencies

Volumes 01–20 (all prior CIOS specifications).
