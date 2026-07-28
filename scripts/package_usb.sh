#!/usr/bin/env bash
# Package current Ceragem CIOS source onto LeFrame_Dev USB for another Mac.
# Creates a versioned folder alongside older packages (e.g. ORION-v1.3.0).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
USB_MOUNT="${USB_MOUNT:-/Volumes/LeFrame_Dev}"
VERSION="${USB_VERSION:-1.4.0}"
USB_ROOT="${USB_ROOT:-$USB_MOUNT/ORION-v$VERSION}"
PREV_USB="${PREV_USB:-$USB_MOUNT/ORION-v1.3.0}"

if [ ! -d "$USB_MOUNT" ]; then
  echo "ERROR: USB '$USB_MOUNT' not mounted. Connect LeFrame_Dev and retry."
  exit 1
fi

if [ -d "$USB_ROOT" ]; then
  echo "ERROR: $USB_ROOT already exists. Set USB_VERSION or remove the folder first."
  exit 1
fi

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
  "$ROOT/" "$USB_ROOT/source/"

echo "==> Copying PostgreSQL backups..."
if [ -d "$ROOT/backend/backups" ] && compgen -G "$ROOT/backend/backups/"* >/dev/null 2>&1; then
  # Prefer flat packaged backups if present locally; else use previous USB package
  if [ -f "$ROOT/backend/backups/database.sql" ]; then
    rsync -a "$ROOT/backend/backups/" "$USB_ROOT/backups/"
  elif [ -d "$PREV_USB/backups" ]; then
    rsync -a "$PREV_USB/backups/" "$USB_ROOT/backups/"
  else
    echo "WARN: No packaged backups found; copy database.sql manually to $USB_ROOT/backups/"
  fi
elif [ -d "$PREV_USB/backups" ]; then
  rsync -a "$PREV_USB/backups/" "$USB_ROOT/backups/"
else
  echo "WARN: No backups copied."
fi

echo "==> Copying docs..."
cp "$ROOT/docs/Local_Operations_Quickstart.md" "$USB_ROOT/docs/"
cp "$ROOT/docs/Other_Mac_Native_Troubleshooting.md" "$USB_ROOT/docs/"
if [ -f "$PREV_USB/docs/Other_Mac_Operations_Guide.md" ]; then
  cp "$PREV_USB/docs/Other_Mac_Operations_Guide.md" "$USB_ROOT/docs/"
fi

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

Version: v$VERSION  (previous USB: ORION-v1.3.0)
Date:    $PACKAGED_AT

OTHER MAC OPERATION: YES (with setup below)

QUICK START
-----------
1. Copy to local Mac (do not run from USB directly):
   cp -R "/Volumes/LeFrame_Dev/ORION-v$VERSION/source" ~/ORION
   mkdir -p ~/ORION/backend/backups
   cp -R "/Volumes/LeFrame_Dev/ORION-v$VERSION/backups/"* ~/ORION/backend/backups/

2. Setup:
   cd ~/ORION
   make setup-local
   make postgres-up
   make migrate
   make restore

3. Start:
   bash scripts/dev.sh start
   # or double-click: Start CIOS.command

4. Login:
   http://127.0.0.1:3002/login
   user@company.com / Ceragem2026!Adm

WHAT'S NEW IN v$VERSION (vs ORION-v1.3.0)
-----------------------------------------
- Login brand motion (7-step ORION sequence)
- Le Frame footer + Privacy / Terms / Legal Notice pages
- Mission Control widget layout updates
- Stable local dev: Start CIOS.command, make dev-daemon

FULL DOCUMENTATION
------------------
docs/Other_Mac_Operations_Guide.md
docs/Other_Mac_Native_Troubleshooting.md
README-USB.md
USB-CHANGES.md

DATA
----
- PostgreSQL backup: backups/ (make restore)
- Upload source files: source/backend/uploads/
- Package size: ~$TOTAL_SIZE (source ~$SOURCE_SIZE)

GitHub: https://github.com/s6b4wkhr99-sketch/ORION
EOF

cat > "$USB_ROOT/README-USB.md" <<EOF
# ORION / Ceragem CIOS — LeFrame_Dev USB

**Version:** v$VERSION · **Date:** $PACKAGED_AT · **Size:** ~$TOTAL_SIZE

> **다른 Mac 운영 가능:** ✅ 소스 + DB 백업 + uploads 포함  
> **이전 USB:** \`ORION-v1.3.0\` (유지됨 — 이 패키지와 구분)

---

## 빠른 시작

\`\`\`bash
cp -R "/Volumes/LeFrame_Dev/ORION-v$VERSION/source" ~/ORION
mkdir -p ~/ORION/backend/backups
cp -R "/Volumes/LeFrame_Dev/ORION-v$VERSION/backups/"* ~/ORION/backend/backups/
cd ~/ORION
make setup-local && make postgres-up && make migrate
make restore
bash scripts/dev.sh start
\`\`\`

**Login:** http://127.0.0.1:3002/login · \`user@company.com\` / \`Ceragem2026!Adm\`

---

## USB 구조

| 경로 | 설명 |
|------|------|
| \`source/\` | ORION v$VERSION 소스 (uploads, data 포함) |
| \`backups/\` | PostgreSQL 백업 (\`make restore\`) |
| \`canvas/\` | Cursor Canvas (README-CANVAS.md) |
| \`docs/\` | 다른 Mac 운영 / 문제 해결 문서 |
| \`USB-CHANGES.md\` | v1.3.0 대비 변경 요약 |

---

## v$VERSION 변경 요약

- 로그인 브랜드 모션 (Le Frame → ORION 5단어 → ORION + Campaign Decision Intelligence)
- Le Frame 푸터, Privacy / Terms / Legal Notice
- Mission Control 위젯 레이아웃 (Recent Opportunities 높이 정렬 등)
- 로컬 개발 안정화 (\`Start CIOS.command\`, \`make dev-daemon\`)

---

## 상세 문서

| 문서 | 용도 |
|------|------|
| \`docs/Other_Mac_Operations_Guide.md\` | 설치·운영 상세 가이드 |
| \`docs/Other_Mac_Native_Troubleshooting.md\` | 문제 발생 시 상황별 해결 |
| \`docs/Local_Operations_Quickstart.md\` | 1페이지 운영 요약 |

GitHub: https://github.com/s6b4wkhr99-sketch/ORION
EOF

cat > "$USB_ROOT/USB-CHANGES.md" <<EOF
# USB Package Changes — v$VERSION ($PACKAGED_AT)

Compared to **ORION-v1.3.0** on the same USB drive.

## UI / Brand

- Login page: 7-step kinetic brand motion (Le Frame logo → ORION words → ORION + tagline)
- Login page: removed role/export helper text; no white card box
- Site footer: Le Frame logo, Copyright, Privacy / Terms / Legal Notice links
- Legal pages: Privacy, Terms, Legal Notice (LG-inspired, CIOS-adapted)

## Mission Control

- Recent Opportunities widget height aligned with Intelligence Score Distribution
- Removed "View Funnel Analysis →" from Revenue Funnel widget

## Local Development

- \`Start CIOS.command\` — persistent Terminal.app server start
- \`make dev-daemon\`, \`make dev-stop\`, \`make dev-status\`, \`make dev-restart\`
- \`scripts/dev_daemon.sh\` — macOS-compatible detached process start

## Package notes

- Folder: \`ORION-v$VERSION\` (do not overwrite v1.3.0)
- Source excludes: \`node_modules\`, \`.next\`, \`.venv\`, \`.dev\` — run \`make setup-local\` on the other Mac
- Includes \`backend/uploads/\` for upload-center continuity
EOF

chmod +x "$USB_ROOT/source/scripts/dev_daemon.sh" 2>/dev/null || true
chmod +x "$USB_ROOT/source/Start CIOS.command" 2>/dev/null || true

echo ""
echo "✓ USB package ready: $USB_ROOT"
du -sh "$USB_ROOT" "$USB_ROOT/source" "$USB_ROOT/backups" 2>/dev/null || true
ls -la "$USB_MOUNT" | grep ORION || true
