#!/usr/bin/env bash
# GitHub SSH key registration helper for ORION push.
set -euo pipefail

KEY_FILE="$HOME/.ssh/id_ed25519"
PUB_FILE="$HOME/.ssh/id_ed25519.pub"

echo "=== CIOS GitHub SSH Key Helper ==="
echo ""

if [ ! -f "$PUB_FILE" ]; then
  echo "Creating new SSH key..."
  mkdir -p "$HOME/.ssh"
  chmod 700 "$HOME/.ssh"
  ssh-keygen -t ed25519 -C "$(whoami)@$(hostname -s)" -f "$KEY_FILE" -N ""
fi

PUB_KEY="$(cat "$PUB_FILE")"

echo "1) Public key (also copied to clipboard):"
echo ""
echo "$PUB_KEY"
echo ""

if command -v pbcopy >/dev/null 2>&1; then
  printf '%s' "$PUB_KEY" | pbcopy
  echo "   ✓ Copied to clipboard (Cmd+V to paste on GitHub)"
fi

echo ""
echo "2) Opening GitHub SSH key page in your default browser..."
echo "   Log in as: s6b4wkhr99-sketch"
echo ""
open "https://github.com/settings/ssh/new"

cat <<'INSTRUCTIONS'

3) On the GitHub page:
   • Title:  Mac CIOS
   • Key type: Authentication Key
   • Key:    Cmd+V (paste from clipboard)
   • Click:  Add SSH key

4) After saving, return here and press Enter to test connection...
INSTRUCTIONS

read -r _

echo ""
echo "Testing GitHub SSH..."
if ssh -o IdentitiesOnly=yes -i "$KEY_FILE" -T git@github.com 2>&1 | grep -qi "successfully authenticated"; then
  echo ""
  echo "✓ SSH key registered successfully!"
  echo ""
  ROOT="$(cd "$(dirname "$0")/.." && pwd)"
  cd "$ROOT"
  git remote set-url origin git@github.com:s6b4wkhr99-sketch/ORION.git
  echo "Pushing to GitHub..."
  git push -u origin main --tags
  echo ""
  echo "✓ Done: https://github.com/s6b4wkhr99-sketch/ORION"
else
  echo ""
  echo "SSH test failed. Check:"
  echo "  • Logged into the correct GitHub account (s6b4wkhr99-sketch)"
  echo "  • Key was pasted completely (starts with ssh-ed25519)"
  echo "  • Run this script again after adding the key"
  exit 1
fi
