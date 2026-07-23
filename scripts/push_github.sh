#!/usr/bin/env bash
# Push CIOS to GitHub (interactive auth in Terminal).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

REMOTE="${1:-https://github.com/s6b4wkhr99-sketch/ORION.git}"

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE"
else
  git remote add origin "$REMOTE"
fi

echo "==> CIOS GitHub Push"
echo "    Remote: $(git remote get-url origin)"
echo "    Branch: $(git branch --show-current)"
echo "    Tags:   $(git tag -l 'v1.1*' | tr '\n' ' ')"
echo ""
echo "If HTTPS auth fails, add this SSH key at https://github.com/settings/ssh/new :"
echo ""
cat ~/.ssh/id_ed25519.pub 2>/dev/null || echo "(no ~/.ssh/id_ed25519.pub — run: ssh-keygen -t ed25519 -N \"\" -f ~/.ssh/id_ed25519)"
echo ""
echo "Then switch remote:"
echo "  git remote set-url origin git@github.com:s6b4wkhr99-sketch/ORION.git"
echo ""

git push -u origin main --tags

echo ""
echo "✓ Push complete: https://github.com/s6b4wkhr99-sketch/ORION"
