# ORION — 다른 Mac 설치 실행 순서 (터미널 Runbook)

**Version:** 1.5.0 · **Updated:** 2026-07-28  
**Package:** `/Volumes/LeFrame_Dev/ORION-v1.5.0`  
**대상:** USB에서 소스를 복사해 **다른 Mac**에 설치·기동할 때 (설치 담당자가 직접 수행)

이 문서는 **위에서 아래로 번호 순서대로** Terminal에 붙여 넣으면 됩니다.  
각 단계 아래 **주의 & Troubleshooting** 은 그 단계에서 자주 나는 문제만 모았습니다.

---

## 시작 전 — 옵션 하나만 고르기

| | **Option A — Full Migration (DB 포함)** | **Option B — System First (업로드)** |
|--|--|--|
| 복사 | `source/` + `backups/` | `source/` 만 |
| DB | `restore` → `migrate` | `migrate` 만 (**restore 금지**) |
| 용도 | 데모·원 Mac과 동일 스냅샷·2.6M 검색 | 캠페인 운영·가벼운 디스크·자체 업로드 |
| 시간 | 30–60분 | 15–25분 (+ 업로드 시간) |

아래 **공통 0~3단계** 후, **Option A는 4A~** / **Option B는 4B~** 로 갈라집니다.

---

## 0. 사전 확인 (다른 Mac)

### 실행

```bash
# 0-1) USB 마운트 확인
ls /Volumes/LeFrame_Dev/ORION-v1.5.0/source/Makefile

# 0-2) Homebrew
brew --version

# 0-3) 디스크 여유 (Option A: 15~20GB+ 권장 / Option B: 5GB+)
df -h ~
```

### 주의 & Troubleshooting

| 증상 | 원인 | 해결 |
|------|------|------|
| `No such file` (USB) | USB 미연결·이름 다름 | Finder에서 `LeFrame_Dev` 확인. 폴더명이 `ORION-v1.5.0`인지 확인 |
| `brew: command not found` | Homebrew 없음 | https://brew.sh 설치 후 터미널 재실행 |
| 디스크 부족 | 복원·`.next`·venv | Option B로 전환하거나 불필요 파일 삭제 |

**필수 소프트웨어 (없으면 이후 단계에서 brew로 설치):**

- Python **3.12** (3.14 불가)
- PostgreSQL **16** (Docker Desktop **또는** Homebrew)
- Node.js (LTS) — `make setup-local` 시 npm 사용

```bash
# (필요 시) 한 번에 설치
brew install python@3.12 postgresql@16 node
```

---

## 1. 프로젝트 복사 (USB → 로컬 SSD)

> USB에서 **직접 실행하지 마세요.** 반드시 `~/ORION`으로 복사합니다.

### 실행 — Option A (DB 포함)

```bash
PKG="/Volumes/LeFrame_Dev/ORION-v1.5.0"

cp -R "$PKG/source" ~/ORION
mkdir -p ~/ORION/backend/backups
cp -R "$PKG/backups/"* ~/ORION/backend/backups/

cd ~/ORION
ls Makefile backend frontend
ls backend/backups/*/database.sql.gz
```

### 실행 — Option B (소스만)

```bash
PKG="/Volumes/LeFrame_Dev/ORION-v1.5.0"

cp -R "$PKG/source" ~/ORION
# backups/ 는 복사하지 않음

cd ~/ORION
ls Makefile backend frontend
```

**(선택) Option B에서 uploads 생략 — 복사 시간·용량 절약**

```bash
PKG="/Volumes/LeFrame_Dev/ORION-v1.5.0"
rm -rf ~/ORION
mkdir -p ~/ORION
rsync -a \
  --exclude 'node_modules/' --exclude '.venv/' --exclude '.next/' \
  --exclude 'backend/uploads/' \
  "$PKG/source/" ~/ORION/
cd ~/ORION
ls Makefile backend frontend
```

### 주의 & Troubleshooting

| 증상 | 원인 | 해결 |
|------|------|------|
| `No rule to make target 'setup-local'` | 잘못된 폴더 | `cd ~/ORION` 후 `ls Makefile` — Makefile이 **바로** 보여야 함 |
| `~/ORION/source/source` 또는 `~/ORION`에 `source/`와 `backend/` 동시 존재 | 패키지 **전체**를 복사함 | `source` **내용**만 `~/ORION` 루트에 두고, 중첩 `source` 폴더 제거. 또는 `cd ~/ORION/source`에서 이후 명령 실행 |
| `database.sql.gz` 없음 (Option A) | backups 미복사 | `cp -R "$PKG/backups/"* ~/ORION/backend/backups/` 재실행 |
| USB `.git` 관련 경고 | USB git HEAD가 파일보다 오래됨 | **무시.** `git reset --hard` **금지** (최신 코드가 날아감) |

**올바른 레이아웃:**

```text
~/ORION/Makefile
~/ORION/backend/
~/ORION/frontend/
~/ORION/scripts/
```

---

## 2. Python 3.12 venv 준비

### 실행

```bash
cd ~/ORION

which python3.12
# Apple Silicon 예: /opt/homebrew/bin/python3.12
# Intel 예:         /usr/local/bin/python3.12

# 이미 잘못된 venv가 있으면 삭제
rm -rf backend/.venv

# which 결과에 나온 경로로 교체
/opt/homebrew/bin/python3.12 -m venv backend/.venv
# Intel: /usr/local/bin/python3.12 -m venv backend/.venv

backend/.venv/bin/python --version
# → Python 3.12.x 이어야 함
```

### 주의 & Troubleshooting

| 증상 | 원인 | 해결 |
|------|------|------|
| `python3.12: No such file` | 3.12 미설치 | `brew install python@3.12` 후 `which python3.12` |
| `SOABI: cpython-314` / pydantic 빌드 실패 | 기본 python이 3.14 | 반드시 `python3.12 -m venv` 로 재생성 |
| `--version`이 3.13/3.14 | 잘못된 인터프리터 | venv 삭제 후 3.12로 재생성 |

---

## 3. 환경 구성 (공통)

### 실행

```bash
cd ~/ORION

make setup-local      # venv pip, backend/.env, frontend npm
make setup-data       # 지도·ACS 참조 (Mission Control 지도용)
make postgres-up      # PostgreSQL 16 @ 127.0.0.1:5432
```

**PostgreSQL PATH (세션마다 필요할 수 있음):**

```bash
# Apple Silicon
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
# Intel
# export PATH="/usr/local/opt/postgresql@16/bin:$PATH"

pg_isready -h 127.0.0.1 -p 5432
# → accepting connections
```

### 주의 & Troubleshooting

| 증상 | 원인 | 해결 |
|------|------|------|
| `alembic: command not found` (이후 단계) | setup-local 미완료·venv 깨짐 | §2로 venv 재생성 → `make setup-local` |
| Docker socket / `docker.sock` 오류 | Docker Desktop 미실행 | Docker Desktop 실행(고래 Running) 후 `make postgres-up` **또는** Homebrew Postgres만 사용 |
| `PostgreSQL is not running` | DB 미기동 | Docker: Desktop 실행. Homebrew: `brew services start postgresql@16` |
| Docker와 brew Postgres를 섞어 씀 | 서로 다른 DB | **하나만** 사용. 데이터가 «사라진 것»처럼 보이면 같은 방식으로만 `postgres-up` |
| `setup-local` 중 npm 오류 | Node 없음·네트워크 | `brew install node` 후 재실행 |
| USB에 `backend/.env` 있음 | 팀 내부 설치용 | 그대로 사용 OK. 외부 전달 USB가 아니면 유지해도 됨 |

---

## 4A. Option A — DB 복원 → 마이그레이션

> **순서 절대 규칙:** `restore` **먼저** → `migrate` **나중**  
> migrate를 먼저 하면 restore가 FK 때문에 실패합니다.

### 실행 4A-1) (권장) 깨끗한 DB

```bash
cd ~/ORION
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
# Intel: export PATH="/usr/local/opt/postgresql@16/bin:$PATH"

psql -h 127.0.0.1 -d postgres <<'SQL'
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'cios' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS cios;
CREATE DATABASE cios OWNER cios;
GRANT ALL PRIVILEGES ON DATABASE cios TO cios;
SQL
```

### 실행 4A-2) restore → migrate

```bash
cd ~/ORION
make restore          # database.sql.gz 자동 해제
make migrate          # alembic → 0019_buyer_source_row_key
```

### 실행 4A-3) 복원 확인

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

**기대 (백업 시점 기준):** `customers` ≈ **2,611,472** · `buyer_purchases` ≈ **5,289**

### 주의 & Troubleshooting

| 증상 | 원인 | 해결 |
|------|------|------|
| `cannot drop constraint raw_upload_pkey` / buyer FK | **migrate를 restore보다 먼저** 실행 | §4A-1 DROP DB → **restore → migrate** 재실행 |
| restore 중 디스크 부족 | ~25GB급 데이터 팽창 | 디스크 확보 후 DROP → restore 재시도 |
| `customers: 0` | restore 실패·다른 Postgres 인스턴스 | `pg_isready` 후 같은 PATH로 DROP→restore. Docker/brew 혼용 확인 |
| `relation "uploads" does not exist` | 테이블명 착오 | 실제 이름: **`raw_upload`** |
| Backend 나중에 `allowed_modules` / `source_row_key` 없음 | migrate 누락 | `make migrate` 후 `bash scripts/dev.sh restart` |
| Alembic head 확인 | — | `cd backend && .venv/bin/alembic current` → **`0019_buyer_source_row_key`** |

→ Option A는 **§5 기동**으로 이동.

---

## 4B. Option B — migrate만 (restore 없음)

### 실행

```bash
cd ~/ORION
make migrate          # NO make restore
```

로그인 계정은 앱 기동 시 seed로 생성됩니다. Mission Control KPI가 **비어 있어도 정상**입니다 (아직 데이터 없음).

### 주의 & Troubleshooting

| 증상 | 원인 | 해결 |
|------|------|------|
| 실수로 `make restore` 실행 | Option B 위반 | DROP DB 후 `make migrate`만 다시 (또는 Option A로 전환) |
| Login 계정 없음 | seed 미실행 | `make init-postgres` 후 `bash scripts/dev.sh restart` |
| Mission Control Load failed | customers=0 | **정상에 가깝음** → §7B에서 Prospect 업로드 |

→ Option B는 **§5 기동** 후 **§7B 업로드**.

---

## 5. 서버 기동

### 실행

```bash
cd ~/ORION
bash scripts/dev.sh start --with-worker
```

**첫 기동:** Next.js가 `frontend/.next`를 만들며 **1–3분** 걸릴 수 있습니다. Terminal 창을 **닫지 마세요.**

### 실행 — 상태 확인

```bash
bash scripts/dev.sh status
curl -s http://127.0.0.1:8000/api/v1/health | head -c 120
echo
curl -s -o /dev/null -w "login HTTP %{http_code}\n" http://127.0.0.1:3002/login
```

**기대:** health에 `"success":true` · login HTTP **200**

### 주의 & Troubleshooting

| 증상 | 원인 | 해결 |
|------|------|------|
| `/login` **Internal Server Error (500)** | `.next` 미생성·삭제 후 미재기동 | `bash scripts/dev.sh restart` 후 1–3분 대기 |
| `ERR_CONNECTION_REFUSED :3002` | Frontend down | `bash scripts/dev.sh start` · Terminal 닫힘 여부 확인 |
| `Servers did not become ready` | Backend migrate/DB | `make migrate` · `tail -80 .dev/logs/backend.log` |
| Port 8000/3002 사용 중 | 이전 프로세스 | `bash scripts/dev.sh stop` 후 재시작 |
| Upload stuck at queued | Worker 없음 | `--with-worker`로 시작 또는 `make worker` |
| Login failed (빨간 글씨) | 대개 Backend 미동작 | `curl :8000/api/v1/health` → 실패 시 `dev.sh start` |
| Invalid credentials | 잠금·해시 | 아래 비밀번호 리셋 스크립트 |

**비밀번호 리셋 (로컬 Admin):**

```bash
cd ~/ORION/backend && source .venv/bin/activate
python << 'EOF'
from app.database import SessionLocal
import app.models
from app.models.user import User
from app.security.password import hash_password
db = SessionLocal()
u = db.query(User).filter(User.email == "user@company.com").first()
if u:
    u.password_hash = hash_password("Ceragem2026!Adm")
    u.failed_login_attempts = 0
    u.locked_at = None
    u.is_active = True
    db.commit()
    print("OK: password reset + unlocked")
else:
    print("user not found — try make init-postgres")
db.close()
EOF
```

---

## 6. 브라우저 로그인 · 설치 검증

### 실행 (브라우저)

1. http://127.0.0.1:3002/login  
2. Email: `user@company.com`  
3. Password: `Ceragem2026!Adm` (대소문자 주의)

### 실행 (터미널 검증 — Option A)

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

### 주의 & Troubleshooting

| 증상 | 원인 | 해결 |
|------|------|------|
| `Failed to fetch` / CORS | `localhost`가 아닌 다른 IP로 접속 | **`http://127.0.0.1:3002`** 사용 |
| Mission Control / Opportunity Finder **Load failed** | customers=0 · migrate 누락 · 첫 로딩 지연 | 아래 「Load failed 복구」 |
| 로그인은 되는데 메뉴 없음 | RBAC | `/admin/users`에서 모듈 권한 (설치자 Admin만) |
| SKU 가격이 원 Mac과 다름 | DB 카탈로그가 백업 시점 | Admin → **SKU Catalog** → 필요 시 **Save & Publish** |

**Load failed 복구 (한 번에):**

```bash
cd ~/ORION
bash scripts/dev.sh stop
pg_isready -h 127.0.0.1 -p 5432 || brew services start postgresql@16
make migrate
# Option A & customers=0 이면:
# make restore && make migrate
bash scripts/dev.sh start --with-worker
# customers 수백만이면 executive 첫 응답 2~5분 대기 후 새로고침
```

---

## 7A. Option A — 운영 체크리스트 (설치 직후)

- [ ] Mission Control KPI 표시
- [ ] Market Intelligence → State 클릭 → **Sellable Products** 표시
- [ ] Metro Intelligence → Sellable Products
- [ ] (선택) Admin → SKU Catalog: MSRP → Promo → Gross, LE Frame 15%
- [ ] 매일: `bash scripts/dev.sh start --with-worker` / 중지: `bash scripts/dev.sh stop`

---

## 7B. Option B — 데이터 업로드 (설치 직후)

### 실행 (브라우저 순서)

| 순서 | 메뉴 | URL |
|------|------|-----|
| 1 | Upload Center (Prospect) | http://127.0.0.1:3002/import |
| 2 | Buyer Upload & GAP | http://127.0.0.1:3002/buyer-import |
| 3 | (선택) SKU Catalog | http://127.0.0.1:3002/admin/catalog |

### 실행 (업로드 후 확인)

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

### 주의 & Troubleshooting

| 증상 | 원인 | 해결 |
|------|------|------|
| Upload queued 고정 | Worker 없음 | `bash scripts/dev.sh start --with-worker` |
| 대용량 업로드 수 시간 | 정상 | subset(주·세그먼트)만 올려 운영 Mac 부하 감소 |
| Purchase Intelligence 빈 화면 | buyer 미업로드 | `/buyer-import` |

---

## 8. 매일 운영 (공통)

```bash
cd ~/ORION

# 시작
bash scripts/dev.sh start --with-worker

# 상태
bash scripts/dev.sh status

# 중지
bash scripts/dev.sh stop

# 재시작 (설정·코드 반영)
bash scripts/dev.sh restart
```

| URL | |
|-----|--|
| Login | http://127.0.0.1:3002/login |
| Mission Control | http://127.0.0.1:3002/mission-control |
| Backend health | http://127.0.0.1:8000/api/v1/health |

**로그:**

```text
~/ORION/.dev/logs/backend.log
~/ORION/.dev/logs/frontend.log
~/ORION/.dev/logs/worker.log
```

### 주의 & Troubleshooting

| 증상 | 해결 |
|------|------|
| Method Not Allowed / 이상한 API | `bash scripts/dev.sh restart` |
| `.next` 삭제 후 500 | `bash scripts/dev.sh restart` (디스크 정리 후 필수) |
| 백업 | `make backup` → `make restore` (순서: restore 후 migrate) |

---

## 9. 한눈에 보는 전체 명령 (복붙용)

### Option A (Full Migration)

```bash
PKG="/Volumes/LeFrame_Dev/ORION-v1.5.0"
cp -R "$PKG/source" ~/ORION
mkdir -p ~/ORION/backend/backups
cp -R "$PKG/backups/"* ~/ORION/backend/backups/
cd ~/ORION

# Python 3.12 (경로를 which python3.12 결과에 맞게)
/opt/homebrew/bin/python3.12 -m venv backend/.venv

make setup-local && make setup-data && make postgres-up
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"

psql -h 127.0.0.1 -d postgres <<'SQL'
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'cios' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS cios;
CREATE DATABASE cios OWNER cios;
GRANT ALL PRIVILEGES ON DATABASE cios TO cios;
SQL

make restore
make migrate
bash scripts/dev.sh start --with-worker
# 브라우저: http://127.0.0.1:3002/login
```

### Option B (System First)

```bash
PKG="/Volumes/LeFrame_Dev/ORION-v1.5.0"
cp -R "$PKG/source" ~/ORION
cd ~/ORION

/opt/homebrew/bin/python3.12 -m venv backend/.venv
make setup-local && make setup-data && make postgres-up
make migrate
bash scripts/dev.sh start --with-worker
# 브라우저 로그인 후 /import → /buyer-import
```

---

## 10. 관련 문서

| 문서 | 용도 |
|------|------|
| **본 문서** `Other_Mac_Install_Runbook.md` | 번호 순 설치 + 단계별 Troubleshooting |
| `Other_Mac_Operations_Guide.md` | 옵션 설명·구조·운영 배경 |
| `Other_Mac_Native_Troubleshooting.md` | 상황별 심화 트러블슈팅 |
| `Local_Operations_Quickstart.md` | 원 Mac 일상 운영 1페이지 |
| `OTHER-MAC-VERIFY.txt` (USB 루트) | 설치 후 체크리스트 |
| `Local_Disk_Cleanup_Guide.md` | `.next` 삭제 등 디스크 정리 |

GitHub: https://github.com/s6b4wkhr99-sketch/ORION
