# Volume 31 — Development Status Report (개발 현황 보고서)

**Version:** 1.1.0  
**Report Date:** 2026-07-23  
**Status:** Local Native Pilot (로컬 네이티브 파일럿)  
**Audience:** 개발자, PM, QA, 운영

---

## 1. 문서 목적

본 문서는 Ceragem CIOS / ORION 플랫폼의 **현재 개발 현황 스냅샷**을 기록합니다.

- [Volume 27](./27_Development_Completion_Specification.md) (v1.0.1, 2026-07-08) 이후 변경 사항 정리
- 로컬 네이티브 운영 완성도 및 알려진 이슈
- 버전 관리 규칙 및 다음 개선 로드맵

**갱신 주칙:** 기능 릴리스 또는 마일스톤 완료 시 본 문서와 `CHANGELOG.md`, 루트 `VERSION` 파일을 함께 업데이트합니다.

---

## 2. 버전 정보

| 항목 | 값 |
|------|-----|
| **애플리케이션 버전** | **1.1.0** |
| 이전 공식 릴리스 | 1.0.1 (2026-07-08) |
| Git baseline | `main` @ `5d07a0b` (2026-07-21 GAP baseline) + 미커밋 로컬 변경 |
| DB 마이그레이션 | Alembic `0018_user_allowed_modules` (head) |
| Frontend | Next.js 16 · `http://127.0.0.1:3002` |
| Backend | FastAPI · `http://127.0.0.1:8000/api/v1` |
| Database | PostgreSQL 16 @ `127.0.0.1:5432/cios` |

### 2.1 버전 관리 (Semantic Versioning)

| 파일 | 역할 |
|------|------|
| [`VERSION`](../VERSION) | **단일 기준 버전** (예: `1.1.0`) |
| [`CHANGELOG.md`](../CHANGELOG.md) | 릴리스별 변경 이력 |
| `backend/app/config.py` → `app_version` | API `/health`, admin dashboard |
| `frontend/src/lib/config.ts` → `APP_VERSION` | UI 표시 |
| Git tag | `v1.1.0` 형식 (릴리스 시 생성) |

**릴리스 절차 (권장)**

1. `VERSION` 및 CHANGELOG 섹션 작성
2. `app_version`, `APP_VERSION`, README 버전 동기화
3. 본 문서(Volume 31) 갱신
4. `git commit` → `git tag v1.1.0` → push (팀 정책에 따름)

**버전 올림 기준**

- **PATCH** (1.1.x): 버그 수정, UX 미세 조정
- **MINOR** (1.x.0): 새 기능·화면·API (하위 호환)
- **MAJOR** (x.0.0): breaking API/DB 변경

---

## 3. v1.1.0 주요 변경 (1.0.1 대비)

### 3.1 ORION UX · Navigation

- Primary nav ORION 워크플로우 명칭 적용 (`Mission Control`, `Market Intelligence`, `Metro Intelligence`, `Opportunity Finder` 등)
- **Administration** 하위 메뉴 순서 확정:
  1. SKU Catalog → 2. Upload Center → 3. Audience Export → 4. Buyer Upload & GAP → 5. User Management → 6. Commercial Simulator → 7. Platform Health
- 사이드바 활성 상태: `/admin/users` 접속 시 Platform Health(`/admin`) 중복 하이라이트 수정

### 3.2 인증 · RBAC · User Management

- JWT 로그인 (`AUTH_REQUIRED=true` 로컬 기본)
- 6개 시스템 역할 + API `require_module` enforcement
- **User Management** (`/admin/users`) 전면 개편:
  - 사용자 선택 → Role menu preview에서 역할·메뉴·프로필 편집
  - 개별 메뉴(href) 단위 custom access (`allowed_modules` JSON)
  - Save/Cancel 명시적 저장 (blur 자동저장 제거)
  - 새 비밀번호: Role menu preview 필드 + Save (prompt 대체)
  - Actions: Disable/Activate, Unlock, **Delete**
- `GET /auth/me` — `modules`, `allowedModules` 반환
- 마이그레이션 `0018_user_allowed_modules.py`

### 3.3 Buyer Upload & GAP · Commercial

- Buyer Upload & GAP (`/buyer-import`) — 마이그레이션 `0016`
- Commercial Simulator forecast 저장 — `0017`
- Audience Export 연동·Commercial Simulator audience upload API

### 3.4 로컬 Dev Ops

- `scripts/dev_foreground.sh` — foreground 안정 실행 (Terminal 유지)
- `Start CIOS.command` → foreground 스크립트
- Backend `uvicorn --reload` (코드 변경 자동 반영)
- Read Only 등 upload 권한 없는 계정: upload list 403 배너 미표시

### 3.5 API 추가

| Method | Path | 설명 |
|--------|------|------|
| DELETE | `/admin/users/{email}` | 사용자 삭제 (본인·마지막 System Admin 보호) |
| (기존) | `/admin/users/*` | create, update, role, reset-password, disable, activate, unlock |

---

## 4. 로컬 네이티브 운영 현황 (2026-07-23)

### 4.1 완성도 요약

| 영역 | 점수 | 비고 |
|------|------|------|
| 핵심 기능 | 7/10 | 업로드→인텔리전스→대시보드→Admin 동작 |
| UI/UX | 6.5/10 | ORION UI 정돈; dev 환경 이슈 잔존 |
| 백엔드 | 8/10 | 테스트·마이그레이션 양호 |
| 프론트엔드 | 6/10 | 자동 E2E 없음 |
| 로컬 운영 편의 | 5/10 | Postgres + worker + Terminal 유지 |
| 보안 (로컬) | 5/10 | dev secret·시드 비밀번호 |
| **종합 (로컬 네이티브)** | **~65–70%** | 내부 파일럿·개발 가능 |

### 4.2 공식 로컬 시작 방법

```bash
# 권장: Start CIOS.command 더블클릭 (Terminal 창 유지)
# 또는:
bash scripts/dev_foreground.sh
```

- Login: http://127.0.0.1:3002/login  
- User Management: http://127.0.0.1:3002/admin/users  
- Health: http://127.0.0.1:8000/api/v1/health  

**System Administrator (로컬 dev):** `user@company.com` / `Ceragem2026!Adm`

Async upload 사용 시 별도 터미널: `make worker`

### 4.3 시드 사용자

| Email | Role |
|-------|------|
| user@company.com | System Administrator |
| manager@company.com | Marketing Manager |
| analyst@company.com | Marketing Analyst |
| data@company.com | Data Administrator |
| exec@company.com | Executive Viewer |
| readonly@company.com | Read Only |

---

## 5. 알려진 이슈 · 제한

| # | 이슈 | 영향 | 우회/상태 |
|---|------|------|-----------|
| 1 | Dev 서버가 Cursor agent 터미널에서 종료됨 | ERR_CONNECTION_REFUSED | `Start CIOS.command` + Terminal 유지 |
| 2 | Backend 코드 변경 후 stale API (reload 전) | 405 Method Not Allowed 등 | 서버 재시작 또는 `--reload` |
| 3 | `window.prompt` / `confirm` 일부 환경 미동작 | Reset password (구) | Role menu preview 비밀번호 필드로 대체 |
| 4 | Upload list API — upload 권한 필요 | Read Only 403 | v1.1.0에서 배너 suppress |
| 5 | 프론트 E2E 테스트 없음 | 회귀 수동 확인 | Phase B 로드맵 |
| 6 | 로컬 PG vs CI SQLite 테스트 불일치 | `make test` 로컬 주의 | test DB 분리 예정 |
| 7 | Upload cancel API 미구현 | Volume 27 §16 | 미착수 |
| 8 | 다중 dev 시작 스크립트 | 혼란 | Phase A 단일화 예정 |

---

## 6. 미커밋 작업 범위 (2026-07-23 기준)

`main` 브랜치에 **로컬 미커밋 변경**이 다수 존재합니다. v1.1.0 태그 전 팀 합의 후 커밋 권장.

**주요 미추적(??) 경로**

- `frontend/src/app/(dashboard)/admin/users/`
- `frontend/src/app/login/`, `frontend/src/contexts/auth-context.tsx`
- `frontend/src/lib/access-control.ts`, `menu-registry.ts`, `route-permissions.ts`
- `frontend/src/app/(dashboard)/buyer-import/`
- `backend/alembic/versions/0016–0018`
- `scripts/dev_foreground.sh`

---

## 7. 다음 개선 로드맵 (제안)

| Phase | 기간 (1명) | 내용 |
|-------|------------|------|
| **A** | 3–5일 | `scripts/dev.sh` 단일화, dev-status 강화, setup_local.sh, README 운영 1페이지 |
| **B** | 1–2주 | Playwright smoke 5–6개, CI frontend job, test DB 분리 |
| **C** | 2–3주 | prod secret, deploy-qa, 문서↔UI 동기화 |

**Phase A 권장 착수 순서:** 기준 고정 → dev.sh → reload/status → env template → E2E smoke

---

## 8. 관련 문서

| 문서 | 용도 |
|------|------|
| [27_Development_Completion_Specification.md](./27_Development_Completion_Specification.md) | v1.0.1 As-Built |
| [CHANGELOG.md](../CHANGELOG.md) | 릴리스 이력 |
| [Local_Operations_Quickstart.md](./Local_Operations_Quickstart.md) | **로컬 운영 1페이지 (v1.1.0)** |
| [28.1_Hybrid_Operations_Plan.md](./28.1_Hybrid_Operations_Plan.md) | 운영·성능 |
| [14_System_Administration_Operations_Manual.md](./14_System_Administration_Operations_Manual.md) | Admin API |
| [AGENTS.md](../AGENTS.md) | 코드·볼륨 매핑 |

---

## 9. 변경 이력 (본 문서)

| Version | Date | Summary |
|---------|------|---------|
| 1.1.0 | 2026-07-23 | Initial status report — ORION nav, User Management, auth/RBAC, local pilot assessment |
