# ORION — 다른 Mac 설치·운영 가이드 (LeFrame_Dev USB)

**Version:** 1.5.0 · **Updated:** 2026-07-28  
**Package:** `LeFrame_Dev` USB · **`ORION-v1.5.0`** (only)  
**GitHub:** https://github.com/s6b4wkhr99-sketch/ORION

---

## 0. 두 가지 설치 옵션 — 먼저 선택하세요

ORION을 다른 Mac에 옮길 때 **목적에 따라** 아래 두 방식 중 하나를 선택합니다.  
**둘 다 공식 지원**하며, USB 패키지(`source/` + 선택적 `backups/`)로 실행 가능합니다.

| | **Option 1 — Full Migration (DB 포함)** | **Option 2 — System First (데이터는 로컬 업로드)** |
|--|--|--|
| **한 줄 요약** | 소스 + PostgreSQL 백업을 함께 복사·복원 | **시스템만** 설치 후, 데이터는 Mac에서 **Upload Center**로 적재 |
| **복사 대상** | `source/` + `backups/` (+ `uploads/` 포함) | `source/` 만 ( `backups/` **생략 가능** ) |
| **DB** | `make restore` → 2.6M+ prospect 즉시 사용 | 빈 DB + `make migrate` → 업로드로 채움 |
| **설치 시간** | 30–60분 (복원 10–20분) | 15–25분 |
| **디스크** | ~4–5 GB+ | ~1–2 GB (대용량 `uploads/` 생략 시) |
| **시스템 안정성** | restore·스키마 충돌 가능 (§7 참고) | **높음** — 최신 migrate만 적용, restore 없음 |
| **검색·탐색 편의** | **즉시** 전체 코hort 검색 | 업로드한 범위만 검색 (필요 데이터만 선택 적재) |
| **적합한 경우** | 파일럿·데모·원 Mac과 **동일 스냅샷** 필요 | 캠페인 운영 Mac, **최신 코드 + 자체 데이터**, USB 용량 절약 |
| **Purchase Intelligence** | 백업에 buyer 데이터 있으면 즉시 | **Buyer Upload & GAP** (`/buyer-import`)에서 CSV 업로드 |
| **Intelligence Pipeline** | restore된 prospect에 이미 적용됨 | Prospect 업로드 후 worker가 처리 (시간 소요) |

### 왜 두 옵션을 나누나?

- **Option 1** — “원 Mac과 **같은 화면·같은 숫자**”가 필요할 때 (경영 데모, QA, 오프라인 전체 검색).
- **Option 2** — “**코드·스키마는 최신**, 데이터는 **운영 Mac에서 통제**”할 때.  
  restore 없이 `migrate`만 하므로 v1.5 스키마(`0019_buyer_source_row_key` 등)와 충돌이 적고,  
  Upload Center / Buyer Upload로 **필요한 cohort만** 넣어 **검색 범위를 가볍게** 유지할 수 있습니다.

> **권장:** 캠페인 운영용 Mac → **Option 2**.  
> 데모·전체 TAM 분석 Mac → **Option 1**.

아래 §1–§6은 공통 사전 요구사항·운영입니다. **§2 = Option 1**, **§3 = Option 2** 설치 절차입니다.

---

## 1. USB 패키지 구조

```
/Volumes/LeFrame_Dev/ORION-vX.Y.Z/
├── START-HERE.txt             ← 옵션별 빠른 시작
├── README-USB.md
├── docs/
│   ├── Other_Mac_Operations_Guide.md   ← 본 문서
│   ├── Other_Mac_Native_Troubleshooting.md
│   └── Local_Operations_Quickstart.md
├── source/                    ← ORION 소스 (필수)
│   ├── backend/
│   │   ├── uploads/           ← Option 1 권장 / Option 2 선택
│   │   └── data/              ← 지도·ACS (Option 2에서도 권장)
│   ├── frontend/
│   ├── scripts/
│   └── Start CIOS.command
├── backups/                   ← Option 1 필수 / Option 2 생략
│   └── YYYYMMDDTHHMMSSZ/
└── canvas/
```

**USB에 없음 (다른 Mac에서 생성):** `node_modules/`, `.next/`, `.venv/`, `.dev/`

### 데이터가 저장되는 위치 (이해 필수)

| 저장소 | 내용 | Option 1 | Option 2 |
|--------|------|----------|----------|
| **PostgreSQL** | customers, intelligence, buyer_purchases | `make restore` | Upload로 적재 |
| **`backend/uploads/`** | 업로드 원본 CSV/XLSX, export 캐시 | USB `source/`에 포함 | 업로드 시 자동 생성 |
| **`backend/data/`** | ZCTA·ACS 지도 참조 | USB 포함 또는 `make setup-data` | `make setup-data` 권장 |

---

## 2. Option 1 — Full Migration (DB 포함)

### 2.1 Step 1 — USB → 로컬 복사

USB에서 **직접 실행하지 마세요.** 로컬 SSD로 복사합니다.

```bash
# 버전 폴더명은 USB에 맞게 변경 (예: ORION-v1.3.1, ORION-v1.5.0)
PKG="/Volumes/LeFrame_Dev/ORION-v1.5.0"

cp -R "$PKG/source" ~/ORION
mkdir -p ~/ORION/backend/backups
cp -R "$PKG/backups/"* ~/ORION/backend/backups/

cd ~/ORION
ls Makefile backend frontend   # 세 항목이 ~/ORION 바로 아래에 있어야 함
```

### 2.2 Step 2 — 환경 구성

```bash
make setup-local      # venv, backend/.env, npm install
make setup-data       # data/가 USB에 있으면 skip 가능
make postgres-up      # PostgreSQL 16 @ 127.0.0.1:5432
```

### 2.3 Step 3 — DB 복원 (순서 중요)

```
① DB 비우기(또는 신규) → ② make restore → ③ make migrate → ④ dev.sh start
```

**restore 전에 migrate 하면 안 됩니다.** (buyer 테이블 등이 생긴 뒤 restore DROP 실패)

```bash
# 신규 Mac / DB 재구성 시 (선택 — 깨끗한 DB)
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"   # Apple Silicon
# Intel: export PATH="/usr/local/opt/postgresql@16/bin:$PATH"

psql -h 127.0.0.1 -d postgres <<'SQL'
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'cios' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS cios;
CREATE DATABASE cios OWNER cios;
GRANT ALL PRIVILEGES ON DATABASE cios TO cios;
SQL

make restore
make migrate
```

**백업 파일:** USB 백업은 **`database.sql.gz`** (압축). `make restore`가 자동 decompress 합니다.  
복원 시 PostgreSQL 데이터 디스크 **~25 GB** 여유가 필요합니다.

### 2.4 Step 4 — 복원 확인 (선택)

```bash
cd ~/ORION/backend && source .venv/bin/activate
python << 'EOF'
from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
print("customers:", f"{db.execute(text('SELECT COUNT(*) FROM customers')).scalar():,}")
print("buyer_purchases:", db.execute(text("SELECT COUNT(*) FROM buyer_purchases")).scalar())
print("raw_upload:", db.execute(text("SELECT COUNT(*) FROM raw_upload")).scalar())
db.close()
EOF
```

기대치: customers **~2,611,472** (백업 시점 기준), buyer_purchases는 v1.4+ 백업에 포함.

### 2.5 Step 5 — 시작·로그인

```bash
bash scripts/dev.sh start --with-worker
```

**첫 기동:** `frontend/.next`가 없으면 Next.js가 **자동 생성**합니다 (1–3분).  
**Internal Server Error (500)** 가 `/login`에 뜨면 → `bash scripts/dev.sh restart` (§7).

| URL | http://127.0.0.1:3002/login |
|-----|-------------------------------|
| Email | `user@company.com` |
| Password | `Ceragem2026!Adm` |

**Terminal 창을 닫지 마세요.** 닫으면 서버가 종료됩니다.

---

## 3. Option 2 — System First (데이터는 로컬 업로드)

### 3.1 Step 1 — 소스만 복사

```bash
PKG="/Volumes/LeFrame_Dev/ORION-v1.5.0"

cp -R "$PKG/source" ~/ORION
# backups/ 는 복사하지 않음

cd ~/ORION
```

대용량 `backend/uploads/`(3 GB+)가 USB `source/`에 포함되어 있어도 **복사는 되지만**,  
로컬에서 새로 업로드할 계획이면 `rsync` 시 `--exclude 'backend/uploads/'` 로 생략 가능:

```bash
rsync -a --exclude 'node_modules/' --exclude '.venv/' --exclude '.next/' \
  --exclude 'backend/uploads/' \
  "$PKG/source/" ~/ORION/
```

### 3.2 Step 2 — 환경 구성 (restore 없음)

```bash
make setup-local
make setup-data       # State/ZIP 지도·income — Mission Control 지도에 필요
make postgres-up
make migrate          # alembic upgrade head (0019_buyer_source_row_key)
```

`make restore` **실행하지 않습니다.**

로그인 계정은 앱 기동 시 `seed_users`로 자동 생성됩니다.  
로그인 실패 시: `make init-postgres` (선택) 후 `bash scripts/dev.sh restart`

### 3.3 Step 3 — 시스템 기동 확인

```bash
bash scripts/dev.sh start --with-worker
bash scripts/dev.sh status
curl -s http://127.0.0.1:8000/api/v1/health
```

로그인 → Mission Control이 **빈 KPI**여도 정상입니다 (아직 데이터 없음).

### 3.4 Step 4 — 데이터 업로드 (로컬 Mac에서)

| 순서 | 메뉴 | URL | 내용 |
|------|------|-----|------|
| 1 | **Upload Center** | http://127.0.0.1:3002/import | Prospect CSV/XLSX — 잠재고객·인텔리전스 파이프라인 |
| 2 | **Buyer Upload & GAP** | http://127.0.0.1:3002/buyer-import | 실구매 CSV — Purchase Intelligence |
| 3 | (선택) SKU Catalog | `/products` | 제품 마스터 |

**Async upload:** `backend/.env`에 `UPLOAD_ASYNC=true`이면 worker 필수:

```bash
bash scripts/dev.sh start --with-worker
# 또는 별도 터미널: make worker
```

**대용량 prospect (수백만 row):**  
- 첫 업로드는 파이프라인 처리에 **수 시간** 걸릴 수 있습니다.  
- 캠페인용 **주·세그먼트 subset**만 올리면 검색·대시보드가 빠릅니다.

**Buyer upload:** v1.5 dedup — 동일 row 재업로드만 skip (`source_row_key`).

### 3.5 Step 5 — 업로드 후 확인

```bash
cd ~/ORION/backend && source .venv/bin/activate
python << 'EOF'
from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
print("customers:", f"{db.execute(text('SELECT COUNT(*) FROM customers')).scalar():,}")
print("buyer_purchases:", db.execute(text("SELECT COUNT(*) FROM buyer_purchases")).scalar())
db.close()
EOF
```

Mission Control · State View · Purchase Intelligence에서 KPI·지도가 채워지는지 확인합니다.

### 3.6 Option 2 → Option 1 전환 (나중에)

전체 DB 스냅샷이 필요해지면:

```bash
bash scripts/dev.sh stop
# §2.3 DB drop → make restore → make migrate → start
```

---

## 4. 사전 요구사항 (공통)

| 항목 | 버전 |
|------|------|
| macOS | 로컬 네이티브 공식 지원 |
| Python | **3.12+** |
| Node.js | **20+** |
| PostgreSQL | **16** (`make postgres-up`) |
| Git | 선택 (GitHub pull 시) |
| Cursor | 선택 (Canvas 가이드) |

**Intel vs Apple Silicon:** Python venv·PostgreSQL PATH가 다릅니다.  
→ [Other_Mac_Native_Troubleshooting.md](./Other_Mac_Native_Troubleshooting.md) §2.3

---

## 5. 매일 운영 (공통)

| 작업 | 명령 |
|------|------|
| 시작 | `bash scripts/dev.sh start` |
| Worker 포함 | `bash scripts/dev.sh start --with-worker` |
| 상태 | `bash scripts/dev.sh status` |
| 재시작 | `bash scripts/dev.sh restart` |
| 중지 | `bash scripts/dev.sh stop` |

### 접속 URL

| 화면 | URL |
|------|-----|
| Login | http://127.0.0.1:3002/login |
| Mission Control | http://127.0.0.1:3002/mission-control |
| Upload Center | http://127.0.0.1:3002/import |
| Buyer Upload & GAP | http://127.0.0.1:3002/buyer-import |
| User Management | http://127.0.0.1:3002/admin/users |
| Backend Health | http://127.0.0.1:8000/api/v1/health |

### 시드 사용자 (로컬 dev)

| Email | Role |
|-------|------|
| user@company.com | System Administrator |
| manager@company.com | Marketing Manager |
| analyst@company.com | Marketing Analyst |
| data@company.com | Data Administrator |
| exec@company.com | Executive Viewer |
| readonly@company.com | Read Only |

---

## 6. 옵션별 체크리스트

### Option 1 — Full Migration

- [ ] Python 3.12+, Node 20+, PostgreSQL 준비
- [ ] USB `source/` + `backups/` 로컬 복사
- [ ] `make setup-local` 완료
- [ ] `make postgres-up` 완료
- [ ] **`make restore` → `make migrate`** 순서 준수
- [ ] customers ~2.6M 확인 (선택)
- [ ] `bash scripts/dev.sh start --with-worker` → login 성공
- [ ] Mission Control KPI 표시 확인

### Option 2 — System First

- [ ] Python 3.12+, Node 20+, PostgreSQL 준비
- [ ] USB `source/` 만 복사 (`backups/` 생략)
- [ ] `make setup-local` + `make setup-data` 완료
- [ ] `make postgres-up` + **`make migrate`만** (restore **안 함**)
- [ ] `bash scripts/dev.sh start --with-worker` → login 성공
- [ ] Upload Center에 prospect 업로드
- [ ] (선택) Buyer Upload & GAP에 구매 CSV 업로드
- [ ] Mission Control / Purchase Intelligence KPI 확인

---

## 7. Option 1 주의 — restore와 migrate

| 실수 | 결과 |
|------|------|
| restore **전에** migrate | `cannot drop constraint raw_upload_pkey` 등 |
| migrate **생략** | v1.5 컬럼 누락 → API 500, Load failed |
| USB 전체를 `~/ORION`에 복사 | `~/ORION/source/source/...` 이중 구조 |
| **`database.sql.gz` 없이 restore** | `database.sql or database.sql.gz missing` — USB `backups/` 재복사 |
| **`.next` 삭제 후 frontend 미재기동** | `/login` 500 Internal Server Error → `dev.sh restart` |

**표준 복구:** [Other_Mac_Native_Troubleshooting.md](./Other_Mac_Native_Troubleshooting.md) §1.3, §3, §5.4

---

## 8. USB vs GitHub

| 소스 | Option 1 | Option 2 |
|------|----------|----------|
| **USB `source/`** | ✅ | ✅ |
| **USB `backups/`** | ✅ 필수 | ❌ 생략 |
| **GitHub** | 코드 갱신용 | **권장** — 최신 v1.5 pull 후 USB `source/` 대체 가능 |

```bash
git clone git@github.com:s6b4wkhr99-sketch/ORION.git ~/ORION
cd ~/ORION && make setup-local && make migrate
# Option 2: 데이터는 /import, /buyer-import
# Option 1: backups만 USB에서 ~/ORION/backend/backups/ 로 복사 후 make restore
```

---

## 9. Canvas · 관련 문서

| 문서 | 용도 |
|------|------|
| [Local_Operations_Quickstart.md](./Local_Operations_Quickstart.md) | 1페이지 운영 요약 |
| [Other_Mac_Native_Troubleshooting.md](./Other_Mac_Native_Troubleshooting.md) | 상황별 문제 해결 |
| `canvas/orion-new-computer-setup.canvas.tsx` | 시각적 설치 체크리스트 |

---

*Ceragem CIOS / ORION · LeFrame_Dev USB · Installation Guide v1.5.0 · 2026-07-28*
