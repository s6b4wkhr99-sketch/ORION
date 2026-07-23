#!/bin/bash
cd "$(dirname "$0")/.."
bash scripts/register_github_ssh.sh
read -n 1 -s -r -p "Press any key to close..."
