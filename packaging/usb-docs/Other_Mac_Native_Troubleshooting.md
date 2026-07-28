# 다른 Mac — 로컬 네이티브 운영 Troubleshooting

**Version:** 1.5.0 · **Updated:** 2026-07-28  
**대상:** USB(`LeFrame_Dev`) 또는 GitHub에서 ORION을 **다른 Mac**에 복사해 네이티브로 운영할 때

이 문서는 실제 다른 Mac(Les-Mac-Pro) 세팅·운영 중 발생한 문제를 **상황별**로 정리했습니다.  
**공식 빠른 시작:** [Local_Operations_Quickstart.md](./Local_Operations_Quickstart.md)

> **v1.5.0 참고:** Alembic head는 `0019_buyer_source_row_key`입니다. USB 패키지 폴더 예: `ORION-v1.5.1/source`.

---

## 0. 먼저 확인 (30초 진단)

모든 문제에서 **아래 4가지**를 먼저 확인하세요.

```bash
cd ~/ORION                 # Makefile 있는 프로젝트 루트 (이중 복사면 ~/ORION/source)
bash scripts/dev.sh status # PostgreSQL / Backend / Frontend / Worker
```

| 확인 | 명령 |
|------|------|
| Python 버전 | `backend/.venv/bin/python --version` → **3.12.x** 여야 함 |
| PostgreSQL | `pg_isready -h 127.0.0.1 -p 5432` |
| Backend | `curl -s http://127.0.0.1:8000/api/v1/health` |
| DB 고객 수 | 아래 「DB 데이터 확인」 참고 |

**DB 데이터 확인:**

```bash
cd ~/ORION/backend && source .venv/bin/activate
python << 'EOF'
from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
print("customers:", f"{db.execute(text('SELECT COUNT(*) FROM customers')).scalar():,}")
print("uploads:", db.execute(text("SELECT COUNT(*) FROM raw_upload")).scalar())
db.close()
EOF
```

> **주의:** 업로드 테이블 이름은 `uploads`가 아니라 **`raw_upload`** 입니다.

---

## 1. USB에서 처음 설치 — 올바른 순서

폴더를 잘못 복사하거나 명령 순서가 틀리면 대부분의 문제가 납니다.

### 1.1 폴더 복사 (USB)

```bash
cp -R "/Volumes/LeFrame_Dev/ORION-v1.5.1/source" ~/ORION
mkdir -p ~/ORION/backend/backups
cp -R "/Volumes/LeFrame_Dev/ORION-v1.5.1/backups/"* ~/ORION/backend/backups/
```

**작업 디렉터리:** `~/ORION` (Makefile, `backend/`, `frontend/`가 **바로** 여기 있어야 함)

❌ 잘못된 예: USB 전체 `ORION-v1.3.0/`를 `~/ORION`에 넣어 `~/ORION/source/source/...` 이중 구조  
✅ 올바른 예: `~/ORION/Makefile`, `~/ORION/backend/`, `~/ORION/frontend/`

### 1.2 최초 1회 설정 순서

```bash
cd ~/ORION
brew install python@3.12 postgresql@16   # 없을 때만
/usr/local/bin/python3.12 -m venv backend/.venv   # Intel Mac 예시 (경로는 아래 §2.3 참고)
make setup-local
brew services start postgresql@16        # Docker 없을 때
make postgres-up                         # Docker 사용 시 Docker Desktop 실행 후
```

### 1.3 DB 복원 순서 (매우 중요)

```
① DB 비우기(또는 신규) → ② make restore → ③ make migrate → ④ dev.sh start
```

| 순서 | 하면 안 되는 이유 |
|------|-------------------|
| **restore 전에 migrate** | 새 테이블(`buyer_purchases` 등)이 생긴 뒤 restore가 DROP에 실패 |
| **migrate 생략** | `users.allowed_modules`, `buyer_purchases.source_row_key` 등 v1.5 컬럼 누락 → Backend/API 500 |

**DB 처음부터 다시 넣기 (표준 절차):**

```bash
cd ~/ORION
export PATH="/usr/local/opt/postgresql@16/bin:$PATH"   # Intel Mac; Apple Silicon은 §2.3

psql -h 127.0.0.1 -d postgres <<'SQL'
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'cios' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS cios;
CREATE DATABASE cios OWNER cios;
GRANT ALL PRIVILEGES ON DATABASE cios TO cios;
SQL

make restore
make migrate
bash scripts/dev.sh start --with-worker
```

---

## 2. 설치·환경 문제

### 2.1 `No rule to make target 'setup-local'`

| 항목 | 내용 |
|------|------|
| **증상** | `make setup-local` 실행 시 위 메시지 |
| **원인** | Makefile이 없는 폴더에서 실행 (보통 `~/ORION` 대신 잘못된 경로) |
| **해결** | `cd ~/ORION` 후 `ls Makefile` 확인. 이중 복사면 `cd ~/ORION/source` 또는 §1.1대로 폴더 정리 |

---

### 2.2 `~/ORION` 안에 `source/` 폴더가 또 있음

| 항목 | 내용 |
|------|------|
| **증상** | `~/ORION`에 `backend/`와 `source/`가 동시에 존재 |
| **원인** | USB 패키지 전체를 그대로 복사 |
| **해결 A (빠름)** | `cd ~/ORION/source` 에서 모든 `make` / `dev.sh` 실행 |
| **해결 B (권장)** | `source/` **내용**을 `~/ORION` 루트로 옮기고 중복 삭제 |

---

### 2.3 Python 3.14 — `pydantic-core` 빌드 실패

| 항목 | 내용 |
|------|------|
| **증상** | `Python reports SOABI: cpython-314-darwin`, `PyO3's maximum supported version (3.13)` |
| **원인** | macOS 기본 `python3`가 3.14 → ORION은 **3.12** 필요 |
| **해결** | |

```bash
cd ~/ORION
brew install python@3.12
rm -rf backend/.venv

# Python 3.12 경로 확인
which python3.12
# Intel Mac (Homebrew):     /usr/local/bin/python3.12
# Apple Silicon (M1/M2/M3): /opt/homebrew/bin/python3.12

/usr/local/bin/python3.12 -m venv backend/.venv    # 경로는 which 결과로 교체
backend/.venv/bin/python --version                 # → Python 3.12.x 확인
make setup-local
```

---

### 2.4 `alembic: command not found`

| 항목 | 내용 |
|------|------|
| **증상** | `make migrate` 시 alembic 없음 |
| **원인** | `make setup-local` 미완료 또는 venv가 3.14로 깨짐 |
| **해결** | §2.3으로 venv 재생성 후 `make setup-local` 완료까지 대기 |

---

### 2.5 PostgreSQL — Docker socket / 연결 실패

| 항목 | 내용 |
|------|------|
| **증상** | `failed to connect to the docker API ... docker.sock` 또는 `PostgreSQL is not running at 127.0.0.1:5432` |
| **원인** | Docker Desktop 미실행, 또는 PostgreSQL 미기동 |
| **해결 A (Docker)** | Docker Desktop 실행 → 고래 아이콘 Running → `make postgres-up` |
| **해결 B (Homebrew)** | `brew install postgresql@16 && brew services start postgresql@16` |

**Docker와 Homebrew PostgreSQL을 번갈아 쓰지 마세요.** 서로 다른 DB 인스턴스라 데이터가 «없어진 것처럼» 보입니다.

---

## 3. DB · 마이그레이션 · 복원

### 3.1 Backend 기동 실패 — `users.allowed_modules does not exist` / API 500

| 항목 | 내용 |
|------|------|
| **증상** | `dev.sh start` → `Servers did not become ready`, backend.log에 `UndefinedColumn: allowed_modules` 또는 `source_row_key` |
| **원인** | 백업(구 스키마) + v1.5 코드 — **migrate 미적용** |
| **해결** | `cd ~/ORION && make migrate && bash scripts/dev.sh restart` |
| **확인** | `cd backend && .venv/bin/alembic current` → head **`0019_buyer_source_row_key`** |

---

### 3.2 `make restore` 실패 — `cannot drop constraint raw_upload_pkey`

| 항목 | 내용 |
|------|------|
| **증상** | `buyer_purchases_upload_id_fkey depends on ... raw_upload_pkey` |
| **원인** | **restore 전에 migrate**를 실행해 새 FK가 생김 |
| **해결** | §1.3 **DB 처음부터 다시 넣기** (DB DROP → restore → migrate) |

---

### 3.3 `relation "uploads" does not exist`

| 항목 | 내용 |
|------|------|
| **증상** | SQL/진단 스크립트에서 `uploads` 테이블 없음 |
| **원인** | 테이블명 착오 — 실제 이름은 `raw_upload` |
| **해결** | `SELECT COUNT(*) FROM raw_upload` 사용. customers=0이면 §1.3 DB 재복원 |

---

### 3.4 DB를 처음부터 다시 올리고 싶을 때

ORION 소스·`backend/uploads/` 파일을 다시 복사할 필요 **없음**. PostgreSQL만 초기화 후 restore.

```bash
cd ~/ORION
# §1.3 DB DROP + restore + migrate + dev.sh start
```

USB 백업만 다시 받을 때:

```bash
cp -R "/Volumes/LeFrame_Dev/ORION-v1.5.1/backups/"* ~/ORION/backend/backups/
```

---

## 4. 로그인 · 인증

### 4.1 `Login failed` (로그인 화면)

| 항목 | 내용 |
|------|------|
| **증상** | 비밀번호 입력 후 빨간 글씨 **Login failed** |
| **원인** | 대부분 **Backend(8000) 미동작** — 비밀번호 문제가 아님 |
| **해결** | |

```bash
curl -s http://127.0.0.1:8000/api/v1/health
cd ~/ORION && bash scripts/dev.sh start
```

`Connection refused` → 서버 터미널을 **닫지 않았는지** 확인.

---

### 4.2 `Invalid credentials`

| 항목 | 내용 |
|------|------|
| **증상** | Login failed 대신 자격 증명 오류 |
| **원인** | 계정 잠금(5회 실패) 또는 restore 후 해시 불일치 |
| **해결** | |

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
db.close()
EOF
```

**로컬 기본 계정:** `user@company.com` / `Ceragem2026!Adm` (대소문자 주의: `Ceragem2026!Adm`)

---

## 5. 대시보드 · UI

### 5.1 상황 — Mission Control · Opportunity Finder 동시 `Load failed`

다른 Mac으로 옮긴 뒤 **로그인은 되는데** 아래 두 화면에서 Load failed / Simulation failed가 **함께** 나오는 경우가 많습니다.

| 화면 | 실패 API | 사용자에게 보이는 메시지 |
|------|----------|-------------------------|
| **Mission Control** | `GET /api/v1/dashboard/executive` | `Failed to load mission control` / Load failed |
| **Opportunity Finder** | `POST /api/v1/campaign/opportunity-simulate` | `Simulation failed` / Load failed |

**왜 동시에 실패하나**

- 두 화면 모두 **Prospect 고객 DB**(`customers` + intelligence rollup)에 의존합니다.
- GitHub clone만 하거나 USB에서 **코드만** 복사하고 `make restore`를 하지 않으면 `customers = 0` → executive API가 실패합니다.
- **migrate 누락**이면 Backend는 떠도 API가 500을 반환합니다.
- **Purchase Radar**(`GET /dashboard/purchases`)만 실패해도 Mission Control **일부** 위젯만 비어 있고, **전체 Load failed**는 보통 executive API 문제입니다.

**브라우저 접속 주의:** `http://127.0.0.1:3002/login` 또는 `http://localhost:3002` 사용. 다른 호스트/IP로 열면 `Failed to fetch — cannot reach the API`가 날 수 있습니다.

---

### 5.2 해결 — Load failed 표준 복구 순서

**1단계 — 30초 진단**

```bash
cd ~/ORION
bash scripts/dev.sh status
pg_isready -h 127.0.0.1 -p 5432
curl -s http://127.0.0.1:8000/api/v1/health
```

§0 **DB 고객 수** 확인 — `customers: 0` 이면 2단계로.

**2단계 — migrate + 재시작 (customers > 0 인데도 실패할 때)**

```bash
cd ~/ORION
make migrate
bash scripts/dev.sh restart
```

**3단계 — DB 재복원 (customers = 0 일 때)**

§1.3 **DB 처음부터 다시 넣기** (`DROP DATABASE` → `make restore` → `make migrate` → `dev.sh start`).

> GitHub에서 clone한 경우: `backend/backups/` SQL이 없으면 Upload Center에서 Prospect 파일을 새로 업로드하거나, USB `backups/`를 복사한 뒤 restore 하세요.

**4단계 — 대용량 DB 첫 로딩**

- `customers`가 **수백만**이면 `GET /dashboard/executive` 첫 응답에 **2~5분** 걸릴 수 있습니다.
- 그 전에 여러 번 새로고침하면 Load failed처럼 보일 수 있으니 **한 번 기다린 뒤** 새로고침하세요.

**5단계 — 로그·Network로 원인 좁히기**

```bash
tail -80 ~/ORION/.dev/logs/backend.log
```

브라우저 **DevTools → Network**에서 `/dashboard/executive`, `/campaign/opportunity-simulate` 의 HTTP status 확인.

| status / 로그 | 의미 | 조치 |
|---------------|------|------|
| `(failed) net::ERR_CONNECTION_REFUSED` | Backend 미동작 | §4.1 `dev.sh start` |
| **401** | 토큰 만료 | 재로그인 |
| **403** | 역할/메뉴 권한 | `/admin/users`에서 `dashboard` 모듈 확인 |
| **500** + `allowed_modules` / `source_row_key` | migrate 누락 | `make migrate` |
| **500** + SQL 오류 | restore/migrate 순서 오류 | §1.3 DB 재복원 |
| **200**인데 UI만 빈 경우 | rollup 빌드 중 | 2~5분 대기 후 새로고침 |

**한 번에 실행 (Load failed 발생 시 권장 순서)**

```bash
cd ~/ORION
bash scripts/dev.sh stop
pg_isready -h 127.0.0.1 -p 5432 || brew services start postgresql@16
make migrate
bash scripts/dev.sh status
# customers = 0 이면: make restore && make migrate
bash scripts/dev.sh start
open http://127.0.0.1:3002/mission-control
```

---

### 5.4 Internal Server Error — `/login` 500 (`.next` 삭제 후)

| 항목 | 내용 |
|------|------|
| **증상** | 브라우저 **Internal Server Error**; `/login` HTTP **500** |
| **로그** | `frontend.log`: `ENOENT ... frontend/.next/dev/server/app/login/page.js` |
| **원인** | 디스크 정리 등으로 **`frontend/.next` 삭제** 후 프론트엔드 **미재기동** |
| **Backend** | `curl http://127.0.0.1:8000/api/v1/health` → **200** (DB·API 정상) |

**해결:**

```bash
cd ~/ORION   # 또는 CIOS 프로젝트 루트
bash scripts/dev.sh restart
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3002/login   # 200 기대
```

상세·정기 디스크 정리: [Local_Disk_Cleanup_Guide.md](./Local_Disk_Cleanup_Guide.md)

---

### 5.3 Market Intelligence — 지도가 거의 회색

| 항목 | 내용 |
|------|------|
| **증상** | 지도만 보이고 주별 데이터 거의 없음 |
| **원인** | DB에 customers/rollup 없음, 또는 Backend 오류 |
| **해결** | §0 customers 확인 → §1.3 restore → 대용량 geo: `make setup-data` (선택) |

---

## 6. 업로드(Import)

### 6.1 Upload가 `queued` / `pending`에서 진행 안 됨

| 항목 | 내용 |
|------|------|
| **증상** | 파일 업로드 후 상태가 queued에서 멈춤 |
| **원인** | `UPLOAD_ASYNC=true`인데 **Worker 미실행** |
| **해결 A** | 새 터미널: `cd ~/ORION && make worker` (창 유지) |
| **해결 B** | 시작 시 Worker 포함: `bash scripts/dev.sh start --with-worker` |
| **해결 C** | Worker 없이 소용량만: `backend/.env`에 `UPLOAD_ASYNC=false` → `dev.sh restart` |

```bash
bash scripts/dev.sh status
# [WARN] Upload worker not running → make worker
```

**Worker 로그:** `.dev/logs/worker.log`

---

## 7. 일상 운영 체크리스트

### 매일 Mac 켤 때

```bash
cd ~/ORION
brew services start postgresql@16          # Homebrew PG 사용 시
bash scripts/dev.sh start --with-worker    # Import 사용 시 Worker 포함 권장
```

브라우저: http://127.0.0.1:3002/login

### 종료할 때

- `dev.sh start` 터미널: **Ctrl+C**
- Worker 터미널: **Ctrl+C**
- 또는: `bash scripts/dev.sh stop`

### 문제 생기면 (순서)

```
dev.sh status → backend.log → customers COUNT → migrate/restore 순서 확인
```

---

## 8. 증상 → 해결 빠른 표

| 증상 | § | 한 줄 해결 |
|------|---|-----------|
| `No rule to make target 'setup-local'` | 2.1 | `cd ~/ORION` (Makefile 있는 폴더) |
| `pydantic-core` / Python 3.14 | 2.3 | Python 3.12 venv 재생성 |
| `docker.sock` / PG not running | 2.5 | Docker 또는 `brew services start postgresql@16` |
| `allowed_modules does not exist` | 3.1 | `make migrate` |
| restore FK 오류 | 3.2 | DB DROP → **restore → migrate** |
| Login failed | 4.1 | `dev.sh start`, Backend 확인 |
| Invalid credentials | 4.2 | 비밀번호 reset 스크립트 |
| Mission Control / Opportunity Finder Load failed | 5.1–5.2 | `dev.sh status` → customers COUNT → restore → migrate → restart |
| `Failed to fetch` / API unreachable | 5.1 | Backend 8000, `127.0.0.1:3002` 접속 |
| Executive 첫 로딩 느림 | 5.2 | customers 많으면 2~5분 대기 |
| Upload queued 멈춤 | 6.1 | `make worker` |
| customers = 0 | 1.3 | `make restore` (migrate **후**가 아님 **전**) |

---

## 9. 로그 · 관련 문서

| 경로 | 내용 |
|------|------|
| `.dev/logs/backend.log` | API / DB 오류 |
| `.dev/logs/frontend.log` | Next.js |
| `.dev/logs/worker.log` | 업로드 큐 |

| 문서 | 용도 |
|------|------|
| [Local_Operations_Quickstart.md](./Local_Operations_Quickstart.md) | 1페이지 운영 요약 |
| [README.md](../README.md) | 프로젝트 개요 |
| USB `canvas/orion-new-computer-setup.canvas.tsx` | Cursor Canvas 시각 가이드 |

---

## 10. 다른 Mac 경로 예시 (Les-Mac-Pro)

| 항목 | 값 |
|------|-----|
| 프로젝트 | `/Users/leframeworkstation/ORION` |
| Python 3.12 | `/usr/local/bin/python3.12` (Intel) |
| PostgreSQL | Homebrew `postgresql@16` @ 127.0.0.1:5432 |
| DB | `cios` / user `cios` |

Apple Silicon Mac에서는 `/opt/homebrew/...` 경로로 바꿔 사용하세요.
