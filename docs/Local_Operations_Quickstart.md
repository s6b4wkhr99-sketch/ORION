# Local Operations Quickstart (로컬 운영 1페이지)

**Version:** 1.3.0 · **Updated:** 2026-07-23

Ceragem CIOS를 Mac에서 **로컬 네이티브**로 운영하는 공식 절차입니다.

---

## 1. 최초 1회 설정

```bash
cd "/Users/josephpark/Website Project/Ceragem Dashboard Project/Ceragem CIOS"

make setup-local      # venv, .env, frontend/.env.local
make postgres-up      # PostgreSQL 16 @ 127.0.0.1:5432
make migrate          # alembic upgrade head
```

또는 macOS: **`Start CIOS.command`** 더블클릭 (PostgreSQL이 이미 떠 있어야 함)

---

## 2. 매일 시작 / 중지

| 작업 | 명령 |
|------|------|
| **시작 (권장)** | `bash scripts/dev.sh start` 또는 **Start CIOS.command** |
| Worker 포함 시작 | `bash scripts/dev.sh start --with-worker` |
| **상태 확인** | `bash scripts/dev.sh status` 또는 `make dev-status` |
| **중지** | `bash scripts/dev.sh stop` 또는 `make dev-stop` |
| **재시작** | `bash scripts/dev.sh restart` |

**중요:** foreground 시작 시 **Terminal 창을 닫지 마세요.** 닫으면 서버가 종료됩니다.

---

## 3. 접속 URL

| 서비스 | URL |
|--------|-----|
| Login | http://127.0.0.1:3002/login |
| Mission Control | http://127.0.0.1:3002/mission-control |
| User Management | http://127.0.0.1:3002/admin/users |
| Backend health | http://127.0.0.1:8000/api/v1/health |

**System Administrator (로컬 dev):** `user@company.com` / `Ceragem2026!Adm`

---

## 4. Upload worker

`backend/.env`에 `UPLOAD_ASYNC=true`이면 **별도 worker**가 필요합니다.

```bash
# 새 Terminal 탭에서
make worker
```

또는 시작 시: `bash scripts/dev.sh start --with-worker`

---

## 5. 자주 나는 문제

| 증상 | 원인 | 해결 |
|------|------|------|
| `ERR_CONNECTION_REFUSED :3002` | Frontend down | `bash scripts/dev.sh start` |
| `Method Not Allowed` (Delete 등) | Stale backend | `bash scripts/dev.sh restart` |
| PostgreSQL error | DB down | `make postgres-up` |
| Upload stuck at queued | Worker 없음 | `make worker` |
| Read Only upload banner | (v1.1.0+) suppressed | 정상 — upload 권한 없음 |
| Login 실패 | AUTH/migrate | `make migrate`, `make setup-local` |
| **Internal Server Error (500) on /login** | `.next` 삭제 후 frontend 미재기동 | `bash scripts/dev.sh restart` — [Local_Disk_Cleanup_Guide.md](./Local_Disk_Cleanup_Guide.md) |

**진단:** `bash scripts/dev.sh status` — PostgreSQL, backend, frontend, worker, API route를 한 번에 확인

**다른 Mac / USB 이전:** 상황별 상세 → [Other_Mac_Native_Troubleshooting.md](./Other_Mac_Native_Troubleshooting.md)

---

## 6. 로그

```text
.dev/logs/backend.log
.dev/logs/frontend.log
.dev/logs/worker.log   (worker 사용 시)
```

---

## 7. 백업 / 복구

```bash
make backup    # → database.sql.gz (평문 sql 자동 제거)
make restore
```

**로컬 디스크 정리** (`.next` 삭제 후 `dev.sh restart` 필수): [Local_Disk_Cleanup_Guide.md](./Local_Disk_Cleanup_Guide.md)

---

## 8. 다른 시작 방법 (비권장)

| 방법 | 비고 |
|------|------|
| `make dev-daemon` | 백그라운드 — Cursor agent 환경에서 불안정할 수 있음 |
| `make backend` + `make frontend` | 수동 2터미널 |
| `run_backend.sh` | deprecated — `dev.sh` 사용 |

**공식 방법은 `scripts/dev.sh` 하나입니다.**

---

## 5. 대용량 데이터 (v1.2.0+)

Git에 포함되지 않는 Census/ACS 파일 — **clone 후 1회:**

```bash
make setup-data
```

| 파일 | 용도 |
|------|------|
| `cb_2020_us_zcta520_500k.zip` | ZCTA choropleth maps |
| `acs2022_5yr_geography.dat` | ZIP income import |

---

## 6. Smoke tests (Phase B)

Requires **running stack** for E2E (`bash scripts/dev.sh start`).

```bash
make test-smoke    # backend — SQLite .test_smoke.db (safe vs local PostgreSQL)
make test-postgres # PostgreSQL migrate + Phase 3 (requires PG @ :5432)
make test-e2e      # frontend — Playwright (5 tests, dev stack running)
make test-ci-e2e   # start backend+frontend + Playwright (PG required)
```

First-time E2E: `cd frontend && npm install && npx playwright install chromium`

---

## 10. 관련 문서

- [Other Mac — Native Troubleshooting](./Other_Mac_Native_Troubleshooting.md) — USB·다른 Mac 상황별 문제 해결
- [Volume 31 — Development Status Report](./31_Development_Status_Report.md)
- [Deploy Prep Quickstart (Phase C)](./Deploy_Prep_Quickstart.md)
- [CHANGELOG.md](../CHANGELOG.md)
- [Volume 27 — As-Built](./27_Development_Completion_Specification.md)
