#!/usr/bin/env bash
# Package current Ceragem CIOS source onto LeFrame_Dev USB for another Mac.
# Creates a versioned folder alongside older packages (e.g. ORION-v1.3.0).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
USB_MOUNT="${USB_MOUNT:-/Volumes/LeFrame_Dev}"
VERSION="${USB_VERSION:-1.5.1}"
USB_ROOT="${USB_ROOT:-$USB_MOUNT/ORION-v$VERSION}"
PREV_USB="${PREV_USB:-$USB_MOUNT/ORION-v1.5.0}"
LATEST_BACKUP="$(find "$ROOT/backend/backups" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | sort | tail -1 || true)"

if [ ! -d "$USB_MOUNT" ]; then
  echo "ERROR: USB '$USB_MOUNT' not mounted. Connect LeFrame_Dev and retry."
  exit 1
fi

if [ -d "$USB_ROOT" ]; then
  echo "WARN: $USB_ROOT already exists — refreshing docs/backups only."
  REFRESH_ONLY=1
else
  REFRESH_ONLY=0
fi

if [ "$REFRESH_ONLY" != "1" ]; then
  echo "==> Packaging ORION v$VERSION to $USB_ROOT"
  mkdir -p "$USB_ROOT"/{source,backups,docs,canvas}

  echo "==> Syncing source (excluding node_modules, .next, .venv, .dev)..."
  rsync -a \
    --exclude 'node_modules/' \
    --exclude '.next/' \
    --exclude 'out/' \
    --exclude 'dist/' \
    --exclude '.venv/' \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '.dev/' \
    --exclude '.DS_Store' \
    --exclude '*.log' \
    --exclude 'backend/.test_smoke.db' \
    --exclude 'backend/backups/' \
    "$ROOT/" "$USB_ROOT/source/"
else
  echo "==> Refreshing ORION v$VERSION on $USB_ROOT"
  mkdir -p "$USB_ROOT"/{source,backups,docs,canvas}
  echo "==> Syncing source (full refresh)..."
  rsync -a \
    --exclude 'node_modules/' \
    --exclude '.next/' \
    --exclude 'out/' \
    --exclude 'dist/' \
    --exclude '.venv/' \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '.dev/' \
    --exclude '.DS_Store' \
    --exclude '*.log' \
    --exclude 'backend/.test_smoke.db' \
    --exclude 'backend/backups/' \
    "$ROOT/" "$USB_ROOT/source/"
fi

echo "==> Copying PostgreSQL backups..."
if [ -n "$LATEST_BACKUP" ] && { [ -f "$LATEST_BACKUP/database.sql" ] || [ -f "$LATEST_BACKUP/database.sql.gz" ]; }; then
  BACKUP_ID="$(basename "$LATEST_BACKUP")"
  mkdir -p "$USB_ROOT/backups/$BACKUP_ID"
  echo "    Latest local backup: $BACKUP_ID"
  rsync -a "$LATEST_BACKUP/env.snapshot" "$USB_ROOT/backups/$BACKUP_ID/"
  if [ -f "$LATEST_BACKUP/uploads.tar.gz" ]; then
    rsync -a "$LATEST_BACKUP/uploads.tar.gz" "$USB_ROOT/backups/$BACKUP_ID/"
  elif [ -f "$USB_ROOT/backups/$BACKUP_ID/uploads.tar.gz" ]; then
    echo "    Keeping existing uploads.tar.gz on USB"
  fi
  if [ -f "$LATEST_BACKUP/database.sql.gz" ]; then
    rsync -a "$LATEST_BACKUP/database.sql.gz" "$USB_ROOT/backups/$BACKUP_ID/"
    echo "    Using database.sql.gz (compressed — restore auto-decompresses)"
  elif [ -f "$LATEST_BACKUP/database.sql" ]; then
    rsync -a "$LATEST_BACKUP/database.sql" "$USB_ROOT/backups/$BACKUP_ID/"
  fi
  cat > "$USB_ROOT/backups/BACKUP-MANIFEST.txt" <<MANIFEST
ORION v$VERSION — PostgreSQL backup manifest
Backup ID: $BACKUP_ID
Packaged: $(date '+%Y-%m-%d %H:%M %Z')

Restore on other Mac:
  cp -R "/Volumes/LeFrame_Dev/ORION-v$VERSION/backups/$BACKUP_ID" ~/ORION/backend/backups/
  cd ~/ORION && make restore && make migrate

Expected counts (source Mac at backup time):
  customers:         ~2,611,472
  customer_intel:    ~2,611,472
  buyer_purchases:   ~5,289
  raw_upload:        ~129
  Alembic after restore+migrate: 0019_buyer_source_row_key

Backup file: database.sql.gz (compressed; make restore auto-decompresses)
MANIFEST
elif [ -f "$ROOT/backend/backups/database.sql" ]; then
  rsync -a "$ROOT/backend/backups/" "$USB_ROOT/backups/"
elif [ -d "$PREV_USB/backups" ]; then
  rsync -a "$PREV_USB/backups/" "$USB_ROOT/backups/"
else
  echo "WARN: No packaged backups found; run 'make backup' then re-package."
fi

echo "==> Copying docs..."
cp "$ROOT/docs/Local_Operations_Quickstart.md" "$USB_ROOT/docs/"
cp "$ROOT/docs/Other_Mac_Install_Runbook.md" "$USB_ROOT/docs/"
cp "$ROOT/docs/Other_Mac_InPlace_Upgrade_Guide.md" "$USB_ROOT/docs/"
cp "$ROOT/docs/Other_Mac_Native_Troubleshooting.md" "$USB_ROOT/docs/"
cp "$ROOT/docs/Other_Mac_Operations_Guide.md" "$USB_ROOT/docs/"
cp "$ROOT/docs/Local_Disk_Cleanup_Guide.md" "$USB_ROOT/docs/"
cp "$ROOT/packaging/usb-docs/START-HERE-INSTALL-OPTIONS.txt" "$USB_ROOT/START-HERE-INSTALL-OPTIONS.txt"
cp "$ROOT/packaging/usb-docs/OTHER-MAC-VERIFY.txt" "$USB_ROOT/OTHER-MAC-VERIFY.txt"

echo "==> Copying canvas..."
if [ -d "$PREV_USB/canvas" ]; then
  rsync -a "$PREV_USB/canvas/" "$USB_ROOT/canvas/"
fi

PACKAGED_AT="$(date '+%Y-%m-%d')"
SOURCE_SIZE="$(du -sh "$USB_ROOT/source" | awk '{print $1}')"
TOTAL_SIZE="$(du -sh "$USB_ROOT" | awk '{print $1}')"

cat > "$USB_ROOT/START-HERE.txt" <<EOF
ORION / Ceragem CIOS — LeFrame_Dev USB Package
==============================================

Version: v$VERSION  (previous USB: ORION-v1.3.1)
Date:    $PACKAGED_AT

OTHER MAC OPERATION: YES — choose ONE install option below.

DATA IN THIS PACKAGE (Option 1)
-------------------------------
  customers:       ~2,611,472 prospects
  buyer_purchases: ~5,289 actual purchases
  Backup folder:   backups/ (see BACKUP-MANIFEST.txt)

INSTALL OPTIONS (see START-HERE-INSTALL-OPTIONS.txt and docs/Other_Mac_Operations_Guide.md)
-------------------------------------------------------------------------------------------

OPTION 1 — Full Migration (DB included)
  cp source + backups → make restore → make migrate → dev.sh start
  Use when: demo / full 2.6M cohort / same snapshot as source Mac

OPTION 2 — System First (upload on local Mac)
  cp source only (skip backups) → make migrate only → dev.sh start
  Then: /import (prospects) and /buyer-import (purchases)
  Use when: campaign ops Mac / latest schema / lighter install

QUICK START — OPTION 1
----------------------
1. cp -R "/Volumes/LeFrame_Dev/ORION-v$VERSION/source" ~/ORION
   mkdir -p ~/ORION/backend/backups
   cp -R "/Volumes/LeFrame_Dev/ORION-v$VERSION/backups/"* ~/ORION/backend/backups/
2. cd ~/ORION && make setup-local && make postgres-up
3. make restore && make migrate
4. bash scripts/dev.sh start --with-worker

QUICK START — OPTION 2
----------------------
1. cp -R "/Volumes/LeFrame_Dev/ORION-v$VERSION/source" ~/ORION
2. cd ~/ORION && make setup-local && make setup-data && make postgres-up
3. make migrate   (NO restore)
4. bash scripts/dev.sh start --with-worker
5. Upload: http://127.0.0.1:3002/import and /buyer-import

Login: http://127.0.0.1:3002/login · user@company.com / Ceragem2026!Adm

FULL DOCUMENTATION
------------------
START-HERE-INSTALL-OPTIONS.txt
docs/Other_Mac_Install_Runbook.md
docs/Other_Mac_InPlace_Upgrade_Guide.md   (upgrade with uploaded data — no restore)
docs/Other_Mac_Operations_Guide.md
docs/Other_Mac_Native_Troubleshooting.md
README-USB.md

DATA
----
Option 1: backups/ (make restore) + source/backend/uploads/
Option 2: upload via UI after start
Package size: ~$TOTAL_SIZE (source ~$SOURCE_SIZE)

GitHub: https://github.com/s6b4wkhr99-sketch/ORION
EOF

cat > "$USB_ROOT/README-USB.md" <<EOF
# ORION / Ceragem CIOS — LeFrame_Dev USB

**Version:** v$VERSION · **Date:** $PACKAGED_AT · **Size:** ~$TOTAL_SIZE

> **다른 Mac 운영 가능:** ✅ 두 가지 설치 옵션 지원  
> **이전 USB:** \`ORION-v1.3.1\` (유지됨 — 이 패키지와 구분)

**Option 1 DB includes:** 2,611,472 prospects + 5,289 buyer purchases (2026-07-28 backup)

---

## 설치 옵션 (하나 선택)

| | **Option 1 — Full Migration** | **Option 2 — System First** |
|--|--|--|
| 복사 | \`source/\` + \`backups/\` | \`source/\` 만 |
| DB | \`make restore\` → \`make migrate\` | \`make migrate\` 만 (업로드로 적재) |
| 적합 | 데모·전체 2.6M 검색 | 캠페인 운영·최신 스키마·가벼운 설치 |

상세: \`START-HERE-INSTALL-OPTIONS.txt\` · \`docs/Other_Mac_Operations_Guide.md\`

---

## Option 1 — 빠른 시작 (DB 포함)

\`\`\`bash
cp -R "/Volumes/LeFrame_Dev/ORION-v$VERSION/source" ~/ORION
mkdir -p ~/ORION/backend/backups
cp -R "/Volumes/LeFrame_Dev/ORION-v$VERSION/backups/"* ~/ORION/backend/backups/
cd ~/ORION
make setup-local && make postgres-up
make restore && make migrate
bash scripts/dev.sh start --with-worker
\`\`\`

## Option 2 — 빠른 시작 (시스템만)

\`\`\`bash
cp -R "/Volumes/LeFrame_Dev/ORION-v$VERSION/source" ~/ORION
cd ~/ORION
make setup-local && make setup-data && make postgres-up
make migrate
bash scripts/dev.sh start --with-worker
# Prospect: http://127.0.0.1:3002/import · Buyer: /buyer-import
\`\`\`

**Login:** http://127.0.0.1:3002/login · \`user@company.com\` / \`Ceragem2026!Adm\`

---

## USB 구조

| 경로 | 설명 |
|------|------|
| \`source/\` | ORION v$VERSION 소스 |
| \`backups/\` | PostgreSQL 백업 — **Option 1만** |
| \`START-HERE-INSTALL-OPTIONS.txt\` | 1페이지 설치 옵션 |
| \`docs/\` | 설치·운영·문제 해결 |
| \`canvas/\` | Cursor Canvas |

---

## 상세 문서

| 문서 | 용도 |
|------|------|
| \`docs/Other_Mac_Install_Runbook.md\` | **번호 순 설치 (Option A/B)** |
| \`docs/Other_Mac_InPlace_Upgrade_Guide.md\` | **업로드 완료 Mac — v1.5.1 업그레이드 (DB 유지)** |
| \`docs/Other_Mac_Operations_Guide.md\` | **설치 옵션 상세 (본 가이드)** |
| \`docs/Other_Mac_Native_Troubleshooting.md\` | 문제 발생 시 상황별 해결 |
| \`docs/Local_Operations_Quickstart.md\` | 1페이지 운영 요약 |

GitHub: https://github.com/s6b4wkhr99-sketch/ORION
EOF

cat > "$USB_ROOT/USB-CHANGES.md" <<EOF
# USB Package Changes — v$VERSION ($PACKAGED_AT)

Compared to **ORION-v1.3.1** on the same USB drive.

## v1.5.1 — In-place upgrade guide & full USB refresh

- \`docs/Other_Mac_InPlace_Upgrade_Guide.md\` — Option B Mac with uploaded data + Load failed → upgrade without \`make restore\`
- Install runbook cross-links; USB folder \`ORION-v1.5.1\` only

## v1.5.0 — Purchase Intelligence & Buyer Upload

- Purchase Intelligence: Purchases by State, Purchase Radar (SKU-level), Brand Loyalty, Product Trust
- Buyer Upload dedup via \`source_row_key\` (migration \`0019\`)
- Mission Control purchase widgets (no Buyer Upload header links)
- ORION DNA feasibility docs; dual install options (Full Migration vs System First)

## v1.4.0 — Purchase Intelligence foundation

- Buyer Upload & GAP (\`/buyer-import\`)
- State×SKU purchase radar backend

## Database in this package

| Table | Rows (approx.) |
|-------|----------------|
| customers | 2,611,472 |
| customer_intelligence | 2,611,472 |
| buyer_purchases | 5,289 |
| raw_upload | 129 |

Backup timestamp: see \`backups/BACKUP-MANIFEST.txt\`

## Restore order (Option 1)

\`\`\`
make restore → make migrate → bash scripts/dev.sh start --with-worker
\`\`\`

Do **not** migrate before restore on a fresh DB.

## Package notes

- Folder: \`ORION-v$VERSION\` (older ORION-v1.3.x folders kept)
- Source excludes: \`node_modules\`, \`.next\`, \`.venv\`, \`.dev\`, \`backend/backups/\`
- Includes \`backend/uploads/\` (~3.2 GB) and \`backend/data/\` for maps
- Run \`make setup-local\` on the other Mac before restore
EOF

chmod +x "$USB_ROOT/source/scripts/dev_daemon.sh" 2>/dev/null || true
chmod +x "$USB_ROOT/source/Start CIOS.command" 2>/dev/null || true

echo ""
echo "✓ USB package ready: $USB_ROOT"
du -sh "$USB_ROOT" "$USB_ROOT/source" "$USB_ROOT/backups" 2>/dev/null || true
ls -la "$USB_MOUNT" | grep ORION || true
