# Volume 08 — Cursor Development Guide

Approved implementation standard for Ceragem CIOS.

## Principles

| ID | Rule |
|----|------|
| 001 | Specification first — follow `/docs` |
| 002 | No new architecture unless requested |
| 003 | Configuration-driven mappings (no hard coding) |
| 004 | Datalogix X/Y/Z/U preserved as strings |
| 005 | Modular, independently maintainable modules |

## Repository Layout

```text
CIOS/frontend/  backend/  docs/  spec/  test/  README.md
```

## Backend Rules

- Routes under `/api/v1`
- Models: `backend/app/models`
- Schemas: `backend/app/schemas`
- Business logic: services (not route handlers)
- Intelligence: `backend/app/segmentation/` (re-exports `app.intelligence`)

## Frontend Rules

- Shared application layout on every page
- TanStack Table for tables
- Recharts for charts
- Responsive layout

## Database Rules

- Raw uploads preserved
- Intelligence stored separately
- Campaign data separate from customer data
- Export history logged
- Campaign report imports auditable

## Logging (Section 18)

System logs: upload, mapping, validation, intelligence generation, campaign creation, export, report import, errors — via `app.utils.audit_log`.

## Error Envelope (Section 17)

Success: `{ "success": true, "data": {} }`  
Failure: `{ "success": false, "message": "..." }`

Global handlers in `app.api.exceptions` registered in `main.py`.

## Development Order

1. Project setup → 2. Database → 3. Upload → 4. Mapping → 5. Customers → 6. Datalogix → 7. Intelligence → 8. Dashboard APIs → 9. Layout → 10–15. Feature pages

## Acceptance Criteria (Section 21)

Upload Excel/CSV, store in DB, preserve Datalogix, generate intelligence, update dashboards, create campaigns, forecast, export, import campaign reports, calculate ROI and Le Frame incentive.

## Cursor Instruction

Proceed in small steps. Do not redesign. Do not add features. Ask only when spec is missing. Prioritize working MVP.

See also: [04_Intelligence_Engine.md](./04_Intelligence_Engine.md), [05_UX_UI_Specification.md](./05_UX_UI_Specification.md), [07_API_Specification.md](./07_API_Specification.md)
