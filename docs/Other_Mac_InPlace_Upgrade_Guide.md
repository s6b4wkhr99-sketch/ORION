# ORION — 다른 Mac 현장 업그레이드 가이드 (데이터 유지)

**Version:** 1.5.1 · **Updated:** 2026-07-28  
**대상:** 다른 Mac에서 **Option B (System First)** 로 설치했고, Prospect/Buyer **업로드는 이미 끝난** 상태에서 **Load failed** 가 나오거나 **최신 v1.5.1** 로 올리려는 경우

**관련 문서**

| 문서 | 용도 |
|------|------|
| [Other_Mac_Install_Runbook.md](./Other_Mac_Install_Runbook.md) | 처음부터 새로 설치 |
| [Other_Mac_Native_Troubleshooting.md](./Other_Mac_Native_Troubleshooting.md) | Load failed 상세 §5 |
| [Other_Mac_Operations_Guide.md](./Other_Mac_Operations_Guide.md) | Option A/B 개요 |

**GitHub 릴리스:** https://github.com/s6b4wkhr99-sketch/ORION/releases/tag/v1.5.1  
**USB 패키지:** `/Volumes/LeFrame_Dev/ORION-v1.5.1`

---

## 0. 이 가이드의 전제

| 항목 | 내용 |
|------|------|
| 설치 방식 | **Option B** — `make restore` **없이** 업로드로 데이터 적재 |
| 데이터 | PostgreSQL에 Prospect(`customers`) / Buyer(`buyer_purchases`) **이미 있음** |
| 목표 | **DB·업로드 데이터는 그대로**, **코드만 v1.5.1** 로 교체 + Load failed 해소 |
| Alembic head | `0019_buyer_source_row_key` (v1.5.1 기준) |

### 절대 하지 말 것 (데이터 삭제됨)

```bash
make restore          # ❌ USB 백업으로 DB 덮어씀 — 업로드분 소실
DROP DATABASE cios;   # ❌ 전체 DB 삭제
git reset --hard      # ❌ .env 등 현장 설정 손실 위험
```

---

## 1. 업그레이드 전 1분 진단

다른 Mac 터미널에서 실행:

```bash
cd ~/ORION    # Makefile, backend/, frontend/ 가 바로 있는 루트
bash scripts/dev.sh status
```

**DB에 데이터가 있는지 확인 (가장 중요):**

```bash
cd ~/ORION/backend && source .venv/bin/activate
python << 'EOF'
from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
for table in ("customers", "raw_upload", "buyer_purchases"):
    try:
        n = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        print(f"{table}: {n:,}")
    except Exception as e:
        print(f"{table}: ERROR — {e}")
db.close()
EOF
```

| 결과 | 의미 |
|------|------|
| `customers > 0` | 업로드 데이터 **있음** → 이 가이드대로 **코드만** 업그레이드 |
| `customers = 0` | DB 비어 있음 → [Install Runbook §7B](./Other_Mac_Install_Runbook.md) 에서 업로드부터 |
| Backend down | `bash scripts/dev.sh start` 후 재시도 |

**현재 코드 버전 확인:**

```bash
cat ~/ORION/VERSION    # 목표: 1.5.1
```

---

## 2. (권장) 업그레이드 전 DB 백업 — 2분

업로드를 이미 마쳤다면 **restore는 하지 않지만**, 코드 교체 전 스냅샷은 권장합니다.

```bash
cd ~/ORION
make backup    # backend/backups/<timestamp>/database.sql.gz 생성
ls -lh backend/backups/*/database.sql.gz | tail -1
```

> 이 백업은 **롤백용**입니다. 업그레이드 후 문제가 없으면 디스크 정리 가능.

---

## 3. 코드 업그레이드 — 방법 A (GitHub, 권장)

현장 Mac에 Git clone으로 설치했거나 `~/ORION` 이 git repo인 경우:

```bash
cd ~/ORION
bash scripts/dev.sh stop

# 현장 설정 백업
cp backend/.env /tmp/orion-backend.env.bak 2>/dev/null || true
cp frontend/.env.local /tmp/orion-frontend.env.local.bak 2>/dev/null || true

git fetch origin
git checkout v1.5.1

# 설정 복원 (checkout이 덮어쓴 경우)
cp /tmp/orion-backend.env.bak backend/.env 2>/dev/null || true
cp /tmp/orion-frontend.env.local.bak frontend/.env.local 2>/dev/null || true

cat VERSION    # → 1.5.1
```

Git이 **없는** USB 복사본만 있는 경우 → **§4 방법 B** 사용.

---

## 4. 코드 업그레이드 — 방법 B (USB `ORION-v1.5.1`)

USB에서 **소스만** 덮어씁니다. **PostgreSQL 데이터·`.env`·venv·업로드 파일** 은 유지합니다.

```bash
PKG="/Volumes/LeFrame_Dev/ORION-v1.5.1"
cd ~/ORION
bash scripts/dev.sh stop

# 현장 설정 백업
cp backend/.env /tmp/orion-backend.env.bak
cp frontend/.env.local /tmp/orion-frontend.env.local.bak 2>/dev/null || true

# 코드 동기 (데이터·환경 제외)
rsync -a \
  --exclude 'node_modules/' \
  --exclude '.next/' \
  --exclude '.venv/' \
  --exclude 'venv/' \
  --exclude '.dev/' \
  --exclude 'backend/backups/' \
  --exclude 'backend/uploads/' \
  --exclude 'backend/.env' \
  --exclude 'frontend/.env.local' \
  --exclude '.git/' \
  "$PKG/source/" ~/ORION/

cp /tmp/orion-backend.env.bak backend/.env
cp /tmp/orion-frontend.env.local.bak frontend/.env.local 2>/dev/null || true

cat VERSION    # → 1.5.1
```

> **`backend/uploads/`** 를 exclude 한 이유: Option B에서 업로드 원본 CSV가 여기 쌓일 수 있어, 덮어쓰기를 방지합니다.

---

## 5. 업그레이드 후 필수 단계 (데이터 유지)

**순서를 지키세요.**

```bash
cd ~/ORION

# 1) 의존성 (requirements/package.json 변경 시)
make setup-local

# 2) 스키마만 최신으로 (restore 아님!)
make migrate

# 3) Buyer 업로드가 있다면 — M6(s) → M6S 토큰 정리 (v1.5.1)
cd backend && source .venv/bin/activate
PYTHONPATH=. python -c "
from app.database import SessionLocal
from app.acquisition.buyer_upload import reparse_buyer_sku_tokens
db = SessionLocal()
print(reparse_buyer_sku_tokens(db))
db.close()
"
cd ~/ORION

# 4) 기동
bash scripts/dev.sh start --with-worker

# 5) 헬스 확인
bash scripts/dev.sh status
curl -s http://127.0.0.1:8000/api/v1/health
curl -s -o /dev/null -w "login HTTP %{http_code}\n" http://127.0.0.1:3002/login
```

---

## 6. Load failed 해소 — 업로드 완료 후에도 실패할 때

로그인은 되는데 **Mission Control / Opportunity Finder** 에 `Load failed` 가 보이면:

### 6.1 흔한 원인 (데이터 있는데도)

| 원인 | 설명 |
|------|------|
| **migrate 누락** | 구 코드 + 신 스키마 불일치 → API 500 |
| **첫 executive 로딩** | customers 수십만~수백만이면 **첫 응답 2~5분** — 성급한 새로고침이 Load failed처럼 보임 |
| **`.next` 삭제 후 미재기동** | `/login` 500, Internal Server Error |
| **잘못된 URL** | `127.0.0.1` 대신 다른 IP → CORS / Failed to fetch |
| **Intelligence 미완료** | 업로드 직후 worker가 rollup 생성 중 |

### 6.2 표준 복구 (DB 유지, restore 없음)

```bash
cd ~/ORION
bash scripts/dev.sh stop
make migrate
bash scripts/dev.sh restart --with-worker
```

브라우저: **http://127.0.0.1:3002/mission-control**  
→ **2~5분** 기다린 뒤 **한 번** 새로고침 (customers 많을 때).

### 6.3 Worker / Intelligence 확인

```bash
# Upload worker 동작 여부
pgrep -fl "app.worker.main" || echo "worker not running — use: bash scripts/dev.sh start --with-worker"

# Intelligence rollup 진행 확인
cd ~/ORION/backend && source .venv/bin/activate
python << 'EOF'
from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
ci = db.execute(text("SELECT COUNT(*) FROM customer_intelligence")).scalar()
cu = db.execute(text("SELECT COUNT(*) FROM customers")).scalar()
pending = db.execute(text("SELECT COUNT(*) FROM raw_upload WHERE status IN ('pending','processing')")).scalar()
print(f"customers: {cu:,}  intelligence: {ci:,}  pending uploads: {pending}")
db.close()
EOF
```

| intelligence vs customers | 조치 |
|---------------------------|------|
| intelligence ≈ customers | 정상 — §6.2 재시작·대기 |
| intelligence << customers | worker 기동 후 **10~30분** 대기 또는 upload 상태 확인 |
| pending uploads > 0 | `/import` 에서 처리 완료될 때까지 대기 |

### 6.4 Network / 로그로 원인 좁히기

```bash
tail -80 ~/ORION/.dev/logs/backend.log
```

브라우저 **DevTools → Network**:

| API | 실패 시 |
|-----|---------|
| `GET /api/v1/dashboard/executive` | Mission Control Load failed |
| `POST /api/v1/campaign/opportunity-simulate` | Opportunity Finder Simulation failed |

| HTTP | 조치 |
|------|------|
| 500 + `allowed_modules` / `source_row_key` | `make migrate` |
| 401 | 재로그인 |
| (failed) connection refused | `bash scripts/dev.sh start` |
| 200인데 UI 빈 화면 | 2~5분 대기 후 새로고침 |

상세: [Other_Mac_Native_Troubleshooting.md §5](./Other_Mac_Native_Troubleshooting.md)

---

## 7. 업그레이드 확인 체크리스트 (v1.5.1)

```bash
cd ~/ORION
cat VERSION                                    # 1.5.1
grep M6S_PRODUCT backend/app/intelligence/buyer_gap_mapping.py | head -1
test -f frontend/src/components/decision/mission-control/mission-control-opportunity-section.tsx && echo "layout OK"
grep SellableProductsSection frontend/src/components/market-intelligence/state-view.tsx | head -1
```

**브라우저**

- [ ] http://127.0.0.1:3002/login — HTTP 200
- [ ] Mission Control — KPI 표시 (첫 로드 2~5분 허용)
- [ ] Opportunity Finder — 시뮬레이션 실행
- [ ] Market Intelligence → State 선택 → **Sellable Products**
- [ ] Purchase Radar — Pause M6s 레전드 (Buyer 업로드 시)

---

## 8. 문제가 계속될 때

| 상황 | 조치 |
|------|------|
| migrate 후에도 500 | `backend.log` 전체 오류 메시지 확인 → [Troubleshooting §5](./Other_Mac_Native_Troubleshooting.md) |
| `/login` 500 | `bash scripts/dev.sh restart` ([§5.4](./Other_Mac_Native_Troubleshooting.md)) |
| customers=0 으로 바뀜 | 실수로 restore/DROP 한 것 — §2 백업에서 **선택적** 복구 (업로드 재업로드보다 백업이 빠를 수 있음) |
| 코드만 롤백 | git checkout `<이전-tag>` 또는 USB 이전 source (DB는 migrate 되돌리기 어려움 — 백업 restore 검토) |

**지원용으로 보낼 정보:**

```bash
cd ~/ORION
bash scripts/dev.sh status 2>&1 | tee /tmp/orion-status.txt
cat VERSION >> /tmp/orion-status.txt
tail -50 .dev/logs/backend.log >> /tmp/orion-status.txt
```

---

## 9. 한 페이지 요약 (복사용)

```bash
# === ORION v1.5.1 현장 업그레이드 (데이터 유지 · Option B) ===
cd ~/ORION && bash scripts/dev.sh stop
make backup
# Git:  git fetch && git checkout v1.5.1
# USB:  rsync -a --exclude node_modules --exclude .next --exclude .venv \
#         --exclude .dev --exclude backend/backups --exclude backend/uploads \
#         --exclude backend/.env --exclude frontend/.env.local \
#         /Volumes/LeFrame_Dev/ORION-v1.5.1/source/ ~/ORION/
make setup-local
make migrate
cd backend && source .venv/bin/activate && PYTHONPATH=. python -c "
from app.database import SessionLocal
from app.acquisition.buyer_upload import reparse_buyer_sku_tokens
db=SessionLocal(); print(reparse_buyer_sku_tokens(db)); db.close()"
cd ~/ORION && bash scripts/dev.sh start --with-worker
# Mission Control: 2~5분 대기 후 http://127.0.0.1:3002/mission-control
```

---

*Ceragem CIOS / ORION · In-Place Upgrade Guide v1.5.1 · 2026-07-28*
