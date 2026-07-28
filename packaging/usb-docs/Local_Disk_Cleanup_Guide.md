# 로컬 디스크 정리 가이드 (Dev Mac)

**Version:** 1.0 · **Updated:** 2026-07-28  
**대상:** Joseph Park 개발 Mac · Ceragem CIOS v1.5.0  
**관련:** [Local_Operations_Quickstart.md](./Local_Operations_Quickstart.md) · [Other_Mac_Native_Troubleshooting.md](./Other_Mac_Native_Troubleshooting.md)

---

## 1. 요약

| 구분 | 용량 (2026-07-28 기준) | 삭제 가능? |
|------|------------------------|------------|
| **PostgreSQL** (`/opt/homebrew/var/postgresql@16`) | ~25 GB | ❌ — Prospect+Buyer **실행 DB** |
| **`backend/backups/`** | 정리 후 ~1.6 GB | △ — `.gz`만 유지 |
| **`backend/uploads/`** | ~3.2 GB | ❌ — Upload Center 원본 |
| **`backend/data/`** | ~470 MB | ❌ — 지도·ACS |
| **`frontend/.next`** | ~350 MB | ✅ — **삭제 후 dev 재기동 필수** |

**정리 후 실측:** 프로젝트 폴더 **41 GB → 6.4 GB** (PostgreSQL 25 GB는 별도).

---

## 2. 안전한 정리 절차 (권장)

```bash
cd "/Users/josephpark/Website Project/Ceragem Dashboard Project/Ceragem CIOS"

# 1) 평문 DB 덤프 삭제 (.gz + USB v1.5.0 + PostgreSQL에 동일 데이터)
rm -f backend/backups/*/database.sql

# 2) 구백업 폴더 (최신 타임스탬프만 유지)
# rm -rf backend/backups/20260707T*

# 3) uploads tar (backend/uploads/ 가 있으면 중복)
rm -f backend/backups/*/uploads.tar.gz

# 4) Legacy SQLite archive (PostgreSQL-only 운영)
rm -rf backend/archive/legacy-sqlite

# 5) Next.js 빌드 캐시 (재생성 가능)
rm -rf frontend/.next

# 6) ⚠️ 필수 — Internal Server Error 방지
bash scripts/dev.sh restart
# 또는: bash scripts/dev.sh stop && bash scripts/dev.sh start --with-worker
```

---

## 3. `.next` 삭제 후 Internal Server Error (500)

### 증상

- 브라우저: **Internal Server Error**
- `frontend.log`: `ENOENT ... frontend/.next/dev/server/app/login/page.js`
- Backend `/api/v1/health` → **200** (백엔드·DB는 정상)

### 원인

`frontend/.next`를 지운 뒤 **프론트엔드 프로세스를 재시작하지 않음**.

### 해결

```bash
bash scripts/dev.sh restart
# 또는 stop → start
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3002/login  # 200 기대
```

---

## 4. 백업 정책 (재발 방지)

`make backup` (`backend/scripts/backup.sh`):

| 동작 | 설명 |
|------|------|
| **`database.sql.gz`만 저장** | 평문 32 GB `database.sql` 자동 삭제 |
| **`uploads.tar.gz` 기본 생략** | 로컬 `backend/uploads/` 있으면 중복 |
| USB/다른 Mac 풀 번들 | `BACKUP_INCLUDE_UPLOADS=true make backup` |

`make restore` — **`database.sql.gz` 자동 decompress** 지원.

---

## 5. USB

- **유지:** `LeFrame_Dev/ORION-v1.5.0` only (~7.8 GB)
- **삭제됨 (2026-07-28):** ORION-v1.3.0, ORION-v1.3.1
- Prospect 1년간 추가 없음 가정 → USB 재패키징 불필요 (Buyer만 주기 업로드)

---

## 6. 데이터 성장 가정 (2026-07-28)

| 항목 | 전망 |
|------|------|
| Prospect | **~1년 추가 없음** |
| 이후 증가 | 현재 대비 **최대 ~10%** |
| PostgreSQL | ~25 GB → ~27 GB (장기) |

---

## 7. 절대 삭제하지 말 것

- PostgreSQL data directory (실행 DB)
- `backend/uploads/` (업로드 원본)
- `backend/data/` (지도)
- `backend/backups/*/database.sql.gz` (유일한 로컬 DB 스냅샷 — USB에도 있음)
