# Changelog

All notable releases of Ceragem CIOS follow [Semantic Versioning](https://semver.org/) and Volume 25 Git Workflow.

## [1.4.0] — 2026-07-28

### Summary

Mission Control Purchase Intelligence — actual buyer purchases on map and SKU-based Purchase Radar.

### Features

- **Purchases by State** choropleth on Mission Control (teal palette, `buyer_purchases` data)
- **Purchase Radar** — state × actual SKU bubbles, top 15 states per SKU
- `GET /api/v1/dashboard/purchases` — purchase KPIs, state rollup, radar payload
- SKU legend labels: Master V*, Master S4, Pause M* (filters by `sku_token`)
- Shared radar layout (`RADAR_PLOT_ASPECT_RATIO`) aligned with Opportunity Radar
- Login brand motion, site footer, legal pages (`/legal/*`)
- USB packaging scripts (`scripts/package_usb.sh`, troubleshooting docs)

### Changed

- Opportunity Radar — top 10 states per product; aspect ratio via shared layout module
- Mission Control purchase widgets — removed Buyer Upload header links
- `Pause M2` purchase mapping fix (M2 no longer merged into Pause M6)

## [1.3.0] — 2026-07-23

### Summary

Playwright E2E in CI, PostgreSQL acceptance job, production deploy workflow.

### Features

- CI **postgres-acceptance** job — alembic + init_postgres + Phase 3 PG tests
- CI **e2e** job — Playwright 5 tests against live backend + frontend (`scripts/run_ci_e2e.sh`)
- `make test-postgres`, `make test-ci-e2e` — local/CI parity
- **Deploy Production** workflow (manual, `DEPLOY` confirm + production env secrets)
- `deploy/scripts/deploy_production.sh`
- [Deploy_Production_Guide.md](./docs/Deploy_Production_Guide.md)

### Changed

- Playwright CI retries → 2, expect timeout 15s
- `docker-build` CI job waits for `e2e` + `test`

## [1.2.0] — 2026-07-23

### Summary

QA/staging deploy pipeline, production secret validation, large data assets moved out of Git, Docker compose CI checks.

### Features

- `scripts/generate_secrets.sh` — JWT + PostgreSQL password generation
- `scripts/validate_deploy_env.sh` — production/staging/qa env validation profiles
- `scripts/setup_data_assets.sh` + `make setup-data` — download Census ZCTA + ACS files
- `scripts/compose_staging_smoke.sh` + `make compose-staging-smoke` — Docker up → validate → down
- `deploy/scripts/deploy_qa.sh` — QA host deploy script
- GitHub Actions **Deploy QA** workflow (`.github/workflows/deploy-qa.yml`)
- CI **staging-config** job — compose + env template validation
- [Deploy_QA_Guide.md](./docs/Deploy_QA_Guide.md)

### Changed

- Large geo/ACS files (87–93 MB) removed from Git tracking — use `make setup-data` after clone
- `deploy/env/*` APP_VERSION → 1.2.0

## [1.1.3] — 2026-07-23

### Summary

CI smoke fix for GitHub Actions, Upload Center cancel UI, documentation sync, GitHub SSH helpers.

### Features

- Upload Center **Recent Uploads** — Cancel button for `pending` uploads (`POST /upload/{id}/cancel`)
- `api.cancelUpload()` frontend client
- `Register GitHub SSH.command` + `scripts/register_github_ssh.sh`, `push_github.sh`

### Bug Fixes

- `run_test_smoke.sh` — works without local `.venv` (CI uses system Python)
- Smoke script sets `UPLOAD_ASYNC=true` consistently

### Documentation

- Volume 31 synced to v1.1.3 (GitHub remote, Phase A/B/C complete, maturity ~75%)

## [1.1.2] — 2026-07-23

### Summary

Phase C deploy prep: upload cancel API, release backup script, CI smoke job, staging compose validation, deploy quickstart.

### Features

- `POST /api/v1/upload/{upload_id}/cancel` — cancel pending async uploads (Volume 27 §16)
- `scripts/backup_release.sh` — versioned `git archive` ZIP for iCloud/offline backup
- `scripts/setup_remote.sh` — configure Git `origin` for first push
- `scripts/validate_compose_staging.sh` — validate Docker Compose staging config
- GitHub Actions `smoke` job runs `make test-smoke` before full acceptance tests
- [Deploy_Prep_Quickstart.md](./docs/Deploy_Prep_Quickstart.md)

### Bug Fixes

- Worker skips uploads cancelled while still `pending` (refresh before claim)

## [1.1.1] — 2026-07-23

### Summary

Phase B regression smoke tests: unified `dev.sh` local ops (1.1.0 follow-up) plus backend SQLite smoke and Playwright E2E.

### Features

- `scripts/dev.sh` — single local start/stop/status/restart entry point
- `scripts/setup_local.sh` — first-time env and dependency setup
- [Local_Operations_Quickstart.md](./docs/Local_Operations_Quickstart.md)
- `make test-smoke` — backend auth/RBAC/user-delete on isolated SQLite
- `make test-e2e` — Playwright smoke (login, Read Only banner, User Management UX, nav)

### Documentation

- Volume 31 and README updated for local ops workflow

## [1.1.0] — 2026-07-23

### Summary

ORION navigation UX, full User Management (RBAC, per-menu access, password reset on save, user delete), buyer upload/GAP, commercial simulator forecast, and local dev stability improvements. Development status documented in **Volume 31**.

### Features

- ORION primary navigation labels and Administration menu order (SKU Catalog → … → Platform Health)
- Login flow with JWT; `/auth/me` returns effective modules and allowed menu hrefs
- User Management overhaul: role/menu preview, Save/Cancel, optional new password on save, user delete API
- Per-user custom menu access via `allowed_modules` (migration `0018`)
- Buyer Upload & GAP page and backend (`0016`)
- Commercial Simulator forecast persistence (`0017`)
- `DELETE /api/v1/admin/users/{email}` with self-delete and last-admin guards
- `scripts/dev_foreground.sh` + `Start CIOS.command` for stable local dev; backend `--reload`

### Bug Fixes

- Sidebar: Platform Health no longer highlighted on `/admin/users` and other `/admin/*` routes
- User table email/name inputs retain focus while typing (stable DataTable columns)
- Read Only users: suppress upload-list forbidden banner when upload permission absent
- Replace non-working `window.prompt` password reset with Role menu preview password field

### Documentation

- **Volume 31** — [31_Development_Status_Report.md](./docs/31_Development_Status_Report.md) (개발 현황 · v1.1.0 baseline)
- Root [`VERSION`](./VERSION) file as single version source

### Known Issues

- Local dev requires PostgreSQL, optional upload worker, and keeping the CIOS Terminal window open
- Frontend automated E2E tests not yet implemented
- Upload cancel API still not implemented (carried from v1.0.1)

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
