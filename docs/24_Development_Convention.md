# Volume 24 — Development Convention

**Version:** 1.0 · **Status:** Final

Mandatory development conventions for Ceragem CIOS. Registry: `backend/app/conventions/registry.py`

---

## 1. Purpose

Ensure every developer and AI coding assistant produces a consistent codebase. No implementation shall violate these conventions.

## 2. General Principles

Readable · Predictable · Modular · Testable · Documented · Metadata Driven

## 3. Architecture Layers

```text
Presentation → Application → Business → Intelligence → Repository → Database
```

Business logic shall never exist in the Presentation Layer.

## 4–8. Naming

| Artifact | Convention |
|----------|------------|
| Files | kebab-case |
| Classes | PascalCase |
| Python variables | snake_case |
| TypeScript variables | camelCase |
| DB tables/columns | snake_case |
| Indexes | idx_table_column |

## 9–12. API & Errors

- REST only under `/api/v1`
- Success: `{ "success": true, "data": {}, "message": "" }`
- Error: `{ "success": false, "error": { "code", "message", "timestamp", "requestId" } }`
- Never expose stack traces

## 13. Logging

Fields: timestamp, request_id, module, user_id, execution_ms, severity, message

## 14–17. Configuration, Rules, Intelligence, Upload

- Config via env vars, reference tables, metadata repository
- Flow: Controller → Service → Business Rule → Repository
- Intelligence fields are immutable (version, do not overwrite)
- Upload: Auto Mapping only (RFC-001) — manual mapping prohibited

## 18–20. UI, Dashboard, Comments

Pages: Header, Breadcrumb, Global Filter, Main Content, Action Panel, Status, Footer

Dashboards: Search, Sort, Filter, Pagination, Export, Drill-down, Responsive

## 21–22. Testing & Git

Unit · Integration · Regression · Business Validation

Commit format: `type(scope): description`

## 23. Prohibited Practices

Hard-coded rules, duplicate logic, SQL in controllers, manual intelligence updates, magic numbers, inconsistent API formats.

## API

- `GET /api/v1/conventions`
- `GET /api/v1/conventions/compliance`

## Tests

```bash
cd backend && python tests/test_volume24_acceptance.py
```
