# Changelog

All notable releases of Ceragem CIOS follow [Semantic Versioning](https://semver.org/) and Volume 25 Git Workflow.

## [1.0.1] — 2026-07-08

### Summary

PostgreSQL scale operations, upload pipeline hardening, EST timezone, dashboard filter fixes, and Upload Center UX improvements. As-Built documentation added as Volume 27.

### Features

- Upload Center Mapping Report collapsible dropdown (collapsed during active upload)
- Global upload filter defaults to largest completed batch (fixes empty Revenue by State)
- Eastern Time (`America/New_York`) across backend timestamps and frontend display
- One-click local backup/restore (`make backup`, `make restore`)
- Legacy SQLite archive script (`make archive-sqlite`)

### Bug Fixes

- Expired JWT no longer blocks uploads when `AUTH_REQUIRED=false`
- Upload progress stuck at 0% (duplicate-skip rows now count toward progress)
- `application/octet-stream` MIME allowed for xlsx/csv
- Preview endpoint missing imports (`is_valid_email`, `normalize_zip`, `normalize_state`)
- `backup.sh` pg_dump URL conversion for PostgreSQL
- Frontend API direct connection to `http://127.0.0.1:8000/api/v1`

### Documentation

- **Volume 27** — [27_Development_Completion_Specification.md](./docs/27_Development_Completion_Specification.md) (개발완료 개발서 / As-Built)

## [1.0.0] — 2026-07-06

### Summary

Initial production-ready release of the Ceragem Customer Intelligence Operating System.

### Features

- Customer upload with RFC-001 Auto Mapping Engine
- Reference Data Library (Volume 22) and intelligence calculation framework
- Executive analytics dashboards and AI recommendation engine
- Campaign operating system and provider export integrations
- Knowledge hub with 25 specification volumes indexed

### Bug Fixes

- Legacy field mapping duplicate validation corrections
- Intelligence framework router import restoration

### Database Changes

- Alembic migrations through `0005_v22_reference_data` and RFC-001 auto mapping tables

### API Changes

- `/api/v1/mapping/*`, `/api/v1/reference/*`, `/api/v1/conventions`, `/api/v1/git-workflow`

### Known Issues

- Frontend admin page has a pre-existing TypeScript build warning unrelated to core workflows

### Documentation Updates

- Volumes 01–25 specification library, `AGENTS.md`, and project README (Volume 23)
