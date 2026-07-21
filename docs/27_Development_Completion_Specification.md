# Volume 27 — Development Completion Specification (개발완료 개발서)

**Version:** 1.0.1  
**Status:** As-Built (구현 완료 기준)  
**Last Updated:** 2026-07-08  
**Audience:** 개발자, 운영자, QA, 프로젝트 관리자

---

## 1. 문서 목적

본 문서는 Ceragem CIOS(Customer Intelligence Operating System) **v1.0** 기준으로 **실제 구현이 완료된 기능**을 개발서(As-Built Specification) 형태로 정리합니다.

- 설계 명세(Volumes 01–26)와 달리, **코드베이스에 존재하는 동작**을 기준으로 작성합니다.
- 로컬 개발·PostgreSQL 2.5M 스케일·운영 백업까지 포함한 **현재 완료 상태**를 한 곳에서 확인할 수 있습니다.
- 신규 개발자 온보딩, 인수인계, QA 테스트 계획, 운영 절차의 기준 문서로 사용합니다.

**관련 문서**

| 문서 | 역할 |
|------|------|
| [README.md](../README.md) | 프로젝트 개요 및 Quick Start |
| [docs/README.md](./README.md) | 명세 라이브러리 인덱스 (Volumes 01–26) |
| [RFC-001](./RFC-001_Customer_Upload_Auto_Mapping.md) | 업로드 자동 매핑 규격 |
| [07_API_Specification.md](./07_API_Specification.md) | API 상세 명세 |
| [14_System_Administration_Operations_Manual.md](./14_System_Administration_Operations_Manual.md) | 운영 매뉴얼 |

---

## 2. 프로젝트 개요

### 2.1 정의

Ceragem CIOS는 고객 데이터 업로드 → 자동 매핑 → 검증 → 인텔리전스 생성 → 대시보드·캠페인·보내기까지 연결하는 **Customer Intelligence Operating System**입니다.

- **CRM이 아님** — 고객 관계 관리가 아닌 인텔리전스·캠페인 의사결정 플랫폼
- **ESP(대량 메일)가 아님** — Klaviyo/Mailchimp 등으로 **보내기**만 지원

### 2.2 핵심 워크플로

```text
Excel/CSV 업로드
    ↓
RFC-001 자동 매핑 (Auto Mapping Engine)
    ↓
데이터 표준화 · 검증
    ↓
고객 DB 저장 (중복 스킵/업데이트)
    ↓
인텔리전스 파이프라인 (Datalogix → ZIP → PRIZM → Ceragem → 추천 → 예측)
    ↓
Executive / State / ZIP / Product 대시보드
    ↓
(선택) Provider Export → 캠페인 실행 → 리포트 임포트 → Learning DB
```

### 2.3 저장소 구조

```text
Ceragem CIOS/
├── frontend/          # Next.js 16 (포트 3002)
├── backend/           # FastAPI (포트 8000)
│   ├── app/           # 애플리케이션 모듈
│   ├── scripts/       # backup, restore, init_postgres
│   └── tests/         # Volume·Phase 회귀 테스트
├── scripts/           # 로컬 운영 스크립트 (backup, worker, 2.5M setup)
├── deploy/            # 환경별 env 및 배포 스크립트
├── docs/              # 명세 및 본 개발서 (Volume 27)
├── sample_data/       # 샘플 CSV
├── Makefile           # postgres, worker, backup 등 단축 명령
├── run_backend.sh
└── run_frontend.sh
```

---

## 3. 기술 스택

| 영역 | 기술 | 버전/비고 |
|------|------|-----------|
| Frontend | Next.js (App Router) | 16.x, 포트 **3002** |
| Frontend | React / TypeScript | 19.x / 5.x |
| Frontend | Tailwind CSS | 4.x |
| Frontend | Recharts, react-simple-maps | 차트·미국 지도 |
| Backend | Python / FastAPI | 3.12 / 0.115.x |
| Backend | SQLAlchemy / Alembic | 2.0 / 마이그레이션 |
| Backend | Pandas / openpyxl | CSV·XLSX 처리 |
| Database | SQLite (로컬 기본) | 소규모 개발 |
| Database | PostgreSQL 16 (프로덕션·2.5M) | Homebrew 또는 Docker |
| Auth | JWT (HS256) + bcrypt | `AUTH_REQUIRED=false` 시 로컬 개발 우회 |
| Async Upload | Worker 프로세스 | `python -m app.worker.main` |

---

## 4. 시스템 아키텍처

### 4.1 백엔드 모듈 맵

| 패키지 | 경로 | 역할 |
|--------|------|------|
| Acquisition | `backend/app/acquisition/` | 업로드, 미리보기, 큐, 롤업 |
| Mapping | `backend/app/mapping/` | RFC-001 자동 매핑 엔진 |
| Processing | `backend/app/processing/` | 검증, 중복 처리, 시드 |
| Intelligence | `backend/app/intelligence/` | 세그먼트·지수·추천·예측 파이프라인 |
| Campaign | `backend/app/campaign/` | 캠페인 OS, Executive Dashboard API |
| Analytics | `backend/app/analytics/` | 분석·스코어카드·알림 |
| Providers | `backend/app/providers/` | Klaviyo/Mailchimp 등 Export |
| Security | `backend/app/security/` | JWT, RBAC, 감사 로그 |
| Worker | `backend/app/worker/` | 비동기 업로드 처리 |
| API | `backend/app/api/` | `/api/v1` 라우터, 인증, 의존성 |
| Utils | `backend/app/utils/` | 타임존, 감사 로그, 공통 유틸 |

### 4.2 프론트엔드 구조

| 영역 | 경로 | 역할 |
|------|------|------|
| Pages | `frontend/src/app/(dashboard)/` | 대시보드·업로드·고객·주·ZIP 등 |
| Layout | `frontend/src/components/layout/` | Sidebar, Header, Filter Panel |
| Upload UI | `frontend/src/components/upload/` | 드롭존, 매핑 리포트, 진행률 |
| API Client | `frontend/src/lib/api.ts` | v1 API 호출·타입 정의 |
| Config | `frontend/src/lib/config.ts` | 네비게이션, 캠페인 모듈 표시 여부 |
| Context | `frontend/src/contexts/filter-context.tsx` | 글로벌 필터·업로드 선택 |

### 4.3 API 응답 규격

모든 v1 API는 다음 봉투(envelope)를 사용합니다 (`backend/app/api/responses.py`).

```json
{ "success": true, "data": { } }
{ "success": false, "message": "오류 메시지" }
```

**Base URL:** `http://127.0.0.1:8000/api/v1`

---

## 5. 구현 완료 기능 목록

### 5.1 고객 데이터 업로드 (Upload Center)

| 기능 | 상태 | 구현 위치 |
|------|------|-----------|
| CSV/XLSX 드래그앤드롭 업로드 | ✅ | `upload-drop-zone.tsx`, `acquisition/upload.py` |
| 업로드 미리보기 (매핑·검증 통계) | ✅ | `preview.py`, `import/page.tsx` |
| RFC-001 자동 매핑 리포트 | ✅ | `mapping/auto_engine.py`, `mapping-report.tsx` |
| 매핑 리포트 접기/펼치기 (드롭다운) | ✅ | `mapping-report.tsx` — 업로드 중 기본 접힘 |
| 검증 요약 (이메일·ZIP·주·중복) | ✅ | `validation-summary.tsx` |
| 동기/비동기 업로드 | ✅ | `UPLOAD_ASYNC` env, `upload_queue.py`, `worker/main.py` |
| 대용량(2.5M) Bulk 프로파일 | ✅ | `upload_options.py`, `.env.postgres` |
| 업로드 진행률 폴링 (최대 6시간) | ✅ | `api.ts`, `upload.py` progress_pct |
| 중복 이메일 스킵 (파일·DB) | ✅ | `processing/duplicate.py` |
| MIME `application/octet-stream` 허용 | ✅ | `upload_validation.py` |

### 5.2 인텔리전스 엔진

| 기능 | 상태 | 구현 위치 |
|------|------|-----------|
| Datalogix X/Y/Z/U 보존 | ✅ | `intelligence/pipeline.py` |
| ZIP Intelligence | ✅ | `intelligence/zip_engine.py` |
| PRIZM Proxy 세그먼트 | ✅ | Reference Data + pipeline |
| Ceragem 상업 세그먼트 | ✅ | pipeline |
| 메시지 방향·구매력·통증·라이프스타일 지수 | ✅ | pipeline |
| AI 추천 (제품·메시지·캠페인·지역) | ✅ | `ai_engine/engine.py` |
| 매출·전환 예측 | ✅ | pipeline forecast 단계 |

### 5.3 대시보드 (Customer Intelligence)

| 화면 | 경로 | API | 상태 |
|------|------|-----|------|
| Executive Dashboard | `/dashboard` | `GET /dashboard/executive` | ✅ |
| Upload Center | `/import` | upload/preview APIs | ✅ |
| Customer Intelligence | `/customers` | `GET /dashboard/customer` | ✅ |
| State Intelligence | `/states` | `GET /dashboard/state` | ✅ |
| ZIP Intelligence | `/zip` | `GET /dashboard/zip` | ✅ |
| Product Intelligence | `/products` | `GET /dashboard/product` | ✅ |
| Settings | `/settings` | `GET /settings` | ✅ |

### 5.4 캠페인·분석 (선택 모듈)

`CUSTOMER_ANALYSIS_ONLY=true` 또는 `NEXT_PUBLIC_SHOW_CAMPAIGN_MODULES=false` 시 네비게이션·라우트에서 숨김.

| 화면 | 경로 | 상태 |
|------|------|------|
| Campaign Center | `/campaign-center` | ✅ (조건부 표시) |
| Campaign Performance | `/campaigns` | ✅ (조건부 표시) |
| ROI Center | `/roi` | ✅ (조건부 표시) |
| Export Center | `/export` | ✅ |
| System Admin | `/admin` | ✅ |

### 5.5 보안·거버넌스

| 기능 | 상태 |
|------|------|
| JWT 로그인/갱신/로그아웃 | ✅ |
| RBAC (6개 역할) | ✅ |
| 감사 로그 (업로드·보내기 등) | ✅ |
| Knowledge Hub API (Volumes 01–26 메타) | ✅ |
| Conventions / Git Workflow / Design Principles API | ✅ |

### 5.6 운영·DevOps

| 기능 | 상태 | 구현 |
|------|------|------|
| Health Check | ✅ | `GET /api/v1/health` |
| PostgreSQL 백업 (pg_dump) | ✅ | `backend/scripts/backup.sh` |
| 원클릭 로컬 백업 | ✅ | `scripts/backup_local.sh` |
| 원클릭 로컬 복원 | ✅ | `scripts/restore_local.sh` |
| Legacy SQLite 아카이브 | ✅ | `scripts/archive_legacy_sqlite.sh` |
| 비동기 Worker | ✅ | `scripts/start_worker.sh` |
| 2.5M PostgreSQL 셋업 | ✅ | `scripts/setup_2_5m_postgres.sh` |
| Docker Compose (dev + postgres) | ✅ | `docker-compose.yml`, `docker-compose.postgres.yml` |

---

## 6. 업로드 파이프라인 상세

### 6.1 단계별 흐름

```text
[1] 파일 선택 (Frontend)
      POST /api/v1/customers/upload/preview
      → 헤더 감지, RFC-001 매핑 리포트, 검증 통계 반환

[2] Upload & Process 확인 (Frontend)
      POST /api/v1/customers/upload
      → 파일 저장 (UPLOAD_DIR)
      → raw_upload 레코드 생성

[3a] 동기 모드 (UPLOAD_ASYNC=false)
      → process_upload() 즉시 실행

[3b] 비동기 모드 (UPLOAD_ASYNC=true)
      → status=pending
      → Worker가 claim_next_pending_upload() 후 process_upload()

[4] process_upload (backend/app/acquisition/upload.py)
      → DataFrame 로드
      → 행별: 중복 검사 → customers/customer_datalogix upsert
      → run_intelligence_pipeline()
      → progress_pct 갱신 (1,000행마다 + duplicates_skipped 반영)
      → status=completed, summary_json 저장

[5] Frontend 폴링
      GET /api/v1/upload/{upload_id} (2초 간격)
      → 완료 시 refreshUploads(), refreshExecutive()
```

### 6.2 Bulk Upload 프로파일 (2.5M)

`backend/.env.postgres` 또는 `make setup-2_5m` 적용 시:

| 설정 | 값 | 효과 |
|------|-----|------|
| `UPLOAD_ASYNC` | `true` | Worker 필수 |
| `BULK_UPLOAD_MODE` | `true` | 대용량 최적화 |
| `BULK_UPLOAD_ROW_THRESHOLD` | `100000` | 10만 행 이상 bulk 적용 |
| `BULK_UPLOAD_SKIP_RAW_ROWS` | `true` | raw_customer_data 미저장 |
| `BULK_UPLOAD_SKIP_FULL_TRACE` | `true` | 전체 trace 생략 |
| `BULK_UPLOAD_SKIP_VERSION_HISTORY` | `true` | 버전 이력 생략 |
| `CUSTOMER_ANALYSIS_ONLY` | `true` | 캠페인 UI 숨김 |

### 6.3 Upload Center UI 동작 (v1.0.1)

| 단계 | UI 동작 |
|------|---------|
| 미리보기 | Mapping Report **펼침**, Validation Summary 표시, Upload & Process 버튼 |
| 업로드 진행 | **진행 패널 우선 표시**, Mapping Report **접힘** (클릭 시 선택적 확인) |
| 완료 | 결과 패널 + Upload Another File |

구현: `frontend/src/app/(dashboard)/import/page.tsx`, `mapping-report.tsx` (`collapsible`, `open`, `onOpenChange`)

---

## 7. 글로벌 필터 및 대시보드 연동

### 7.1 업로드 선택 로직

사이드바 필터의 기본 업로드는 **가장 많은 행을 가진 completed 업로드**를 선택합니다. failed·빈 배치는 제외합니다.

```text
frontend/src/lib/upload-selection.ts
  pickDefaultUploadId()  → completed + rows > 0 중 최대
  isUploadUsable()       → failed 제외
```

**적용 위치:** `filter-context.tsx`, `filter-panel.tsx`, Executive/State 대시보드

### 7.2 Revenue by State 빈 데이터 이슈 (해결됨)

- **원인:** 사이드바가 failed 또는 최신(빈) 업로드를 자동 선택 → State Intelligence 데이터 없음
- **해결:** `pickDefaultUploadId()` 도입, 대시보드에 스코프 업로드 데이터 없음 경고

---

## 8. 타임존 (EST/EDT)

애플리케이션 기본 타임존: **America/New_York** (Eastern Time, EST/EDT 자동 전환)

| 영역 | 구현 |
|------|------|
| 환경 변수 | `APP_TIMEZONE=America/New_York` (`.env`, `.env.postgres`, `.env.example`) |
| Backend | `backend/app/utils/timezone.py` — `now_app()`, `format_app_datetime()`, `iso_app()` |
| 적용 API | Health, Executive Dashboard, 업로드 타임스탬프, 감사 로그, 백업 폴더명 |
| Frontend | `formatDateTimeEST()` in `frontend/src/lib/utils.ts` |

---

## 9. 인증 (Auth)

### 9.1 로컬 개발 기본값

```text
AUTH_REQUIRED=false
기본 계정: user@company.com / Ceragem2026!Adm
```

만료된 JWT가 있어도 `AUTH_REQUIRED=false`이면 dev identity로 업로드 허용 (`backend/app/api/deps.py`).

### 9.2 역할 (RBAC)

System Administrator · Marketing Manager · Marketing Analyst · Data Administrator · Executive Viewer · Read Only

---

## 10. 주요 API 엔드포인트 요약

상세: [07_API_Specification.md](./07_API_Specification.md)

### 업로드

| Method | Path | 설명 |
|--------|------|------|
| POST | `/customers/upload/preview` | 미리보기·매핑 리포트 |
| POST | `/customers/upload` | 업로드 실행 |
| GET | `/uploads` | 업로드 목록 |
| GET | `/upload/{upload_id}` | 단건 상태·진행률 |
| GET | `/uploads/processing-profile` | Bulk 프로파일 정보 |
| DELETE | `/upload/{upload_id}` | 업로드 삭제 |

### 대시보드

| Method | Path |
|--------|------|
| GET | `/dashboard/executive` |
| GET | `/dashboard/customer` |
| GET | `/dashboard/state` |
| GET | `/dashboard/zip` |
| GET | `/dashboard/product` |
| GET | `/dashboard/roi` |
| GET | `/dashboard/campaigns` |

### 기타

| Method | Path |
|--------|------|
| POST | `/auth/login` |
| GET | `/health` |
| GET | `/mapping/fields` |
| POST | `/export` |
| POST | `/report/upload` |

---

## 11. 데이터베이스 개요

ORM: `backend/app/models/`

| 테이블 | 용도 |
|--------|------|
| `raw_upload` | 업로드 작업 (pending/processing/completed/failed) |
| `raw_customer_data` | 원본 행 JSON (bulk 모드에서 생략 가능) |
| `customers` | 고객 마스터 |
| `customer_datalogix` | Datalogix 코드 |
| `customer_intelligence` | 세그먼트·지수·추천·예측 |
| `zip_intelligence` | ZIP 참조 |
| `field_master`, `field_alias`, `provider_template` | RFC-001 매핑 사전 |
| `campaign`, `campaign_report_upload` | 캠페인·리포트 |
| `users`, `audit_log` | 사용자·감사 |
| Reference Data (30+ tables) | Volume 22 마스터 데이터 |

**마이그레이션:** `cd backend && alembic upgrade head`

---

## 12. 환경 변수

템플릿: [`.env.example`](../.env.example) → `backend/.env` 복사

| 변수 | 로컬 기본 | PostgreSQL 2.5M |
|------|-----------|-------------------|
| `DATABASE_URL` | SQLite | `postgresql+psycopg2://cios:...@127.0.0.1:5432/cios` |
| `UPLOAD_ASYNC` | `false` | `true` |
| `BULK_UPLOAD_MODE` | `false` | `true` |
| `AUTH_REQUIRED` | `false` | `false` |
| `APP_TIMEZONE` | `America/New_York` | 동일 |
| `CUSTOMER_ANALYSIS_ONLY` | `false` | `true` |

**Frontend** (`frontend/.env.local`):

| 변수 | 설명 |
|------|------|
| `NEXT_PUBLIC_API_URL` | API 베이스 (브라우저: `http://127.0.0.1:8000`) |
| `NEXT_PUBLIC_SHOW_CAMPAIGN_MODULES` | `true`/`false` — 캠페인 네비 표시 |

---

## 13. 실행 가이드

### 13.1 기본 로컬 개발

```bash
# Backend :8000
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd .. && ./run_backend.sh

# Frontend :3002
cd frontend && npm install && cd .. && ./run_frontend.sh
```

브라우저: `http://127.0.0.1:3002`

### 13.2 PostgreSQL + Worker (대용량 업로드)

```bash
make setup-2_5m          # PostgreSQL 초기화 + .env.postgres 적용
make worker              # 비동기 워커 시작 (별도 터미널)
make backend             # API 서버
```

### 13.3 백업·복원

```bash
make backup              # DB dump + uploads + .env 스냅샷
make restore             # 최신 백업 복원 (--yes)
make archive-sqlite      # 레거시 SQLite 아카이브
```

백업 경로: `backend/backups/{timestamp}/`

### 13.4 회귀 테스트

```bash
cd backend && source .venv/bin/activate
python tests/run_acceptance.py    # Volumes 12–26 + Phase 1–3
make test-phase3                  # PostgreSQL 전용 테스트
```

---

## 14. v1.0.1 개발·수정 이력 (As-Built 변경)

| 일자 | 영역 | 변경 내용 | 관련 파일 |
|------|------|-----------|-----------|
| 2026-07 | Backup | `pg_dump` URL 수정 (SQLAlchemy → postgresql://) | `backend/scripts/backup.sh` |
| 2026-07 | Backup | 원클릭 backup/restore 스크립트 | `scripts/backup_local.sh`, `restore_local.sh` |
| 2026-07 | DB | Legacy SQLite ~928MB 아카이브 | `scripts/archive_legacy_sqlite.sh` |
| 2026-07 | Upload | 만료 JWT + `AUTH_REQUIRED=false` 시 업로드 차단 해제 | `api/deps.py` |
| 2026-07 | Upload | 진행률 0% 고정 수정 (duplicates_skipped 반영, 1k마다 갱신) | `upload.py`, `upload_queue.py` |
| 2026-07 | Upload | `application/octet-stream` MIME 허용 | `upload_validation.py` |
| 2026-07 | Upload | preview 누락 import 수정 | `preview.py` |
| 2026-07 | Frontend | API 직접 연결 (`127.0.0.1:8000`) | `api.ts` |
| 2026-07 | Dashboard | 기본 업로드 선택 로직 (completed·최대 행) | `upload-selection.ts`, `filter-context.tsx` |
| 2026-07 | Dashboard | Revenue by State 빈 데이터 경고 | `dashboard/page.tsx` |
| 2026-07 | Timezone | EST/EDT (`America/New_York`) 전역 적용 | `timezone.py`, `utils.ts` |
| 2026-07 | UX | Mapping Report 드롭다운 (업로드 중 접힘) | `mapping-report.tsx`, `import/page.tsx` |
| 2026-07 | Config | Customer Analysis Only — 캠페인 네비/라우트 숨김 | `config.ts`, `middleware.ts` |

---

## 15. 테스트 현황

`backend/tests/run_acceptance.py`에 등록된 주요 스위트:

| 스위트 | 검증 대상 |
|--------|-----------|
| `test_rfc001_acceptance.py` | RFC-001 자동 매핑 |
| `test_phase1_scale.py` | 스케일·Bulk 옵션 |
| `test_phase2_async_upload.py` | 비동기 큐·Worker |
| `test_phase3_postgres.py` | PostgreSQL 통합 |
| `test_upload_profile.py` | Processing profile API |
| `test_duplicate_skip.py` | 중복 스킵 |
| `test_volume08`–`26` | Volume별 수용 기준 |
| `test_executive_dashboard.py` | Executive API |

---

## 16. 알려진 이슈 및 제한

| 항목 | 설명 |
|------|------|
| 업로드 취소 API | `POST /upload/{id}/cancel` 미구현 — DB `pending`/`processing` 수동 변경 또는 Worker 중지 필요 |
| Frontend Admin | TypeScript 빌드 경고 (핵심 워크플로우와 무관) |
| 브라우저 업로드 타임아웃 | 대용량 파일은 async + Worker 사용 권장; proxy timeout 시 Recent Uploads에서 확인 |
| Recent Uploads 키 중복 | 동일 시각 업로드 시 React key 경고 (표시용, 기능 영향 없음) |

---

## 17. 인수인계 체크리스트

- [ ] `backend/.env` 또는 `.env.postgres` 확인
- [ ] PostgreSQL 사용 시 Worker 프로세스 실행 중인지 확인
- [ ] `make backup`으로 백업 절차 검증
- [ ] Upload Center에서 샘플 CSV 업로드 → Executive Dashboard KPI 반영 확인
- [ ] State Intelligence에서 Revenue by State 데이터 표시 확인
- [ ] `python tests/run_acceptance.py` 통과 확인
- [ ] `AUTH_REQUIRED` 프로덕션 전 `true` 전환 및 `JWT_SECRET` 변경

---

## 18. 문서 변경 이력

| 버전 | 일자 | 변경 |
|------|------|------|
| 1.0.1 | 2026-07-08 | Volume 27 최초 작성 — As-Built 개발완료 개발서 |
| 1.0.0 | 2026-07-06 | v1.0.0 릴리스 (CHANGELOG) |

---

*본 문서는 구현 완료 시점의 코드베이스를 기준으로 작성되었습니다. 명세 변경 시 Volumes 01–26 및 RFC-001을 우선하며, 구현 차이는 본 문서를 갱신하여 추적합니다.*
