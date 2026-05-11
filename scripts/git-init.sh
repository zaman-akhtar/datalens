#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -d .git ]; then echo "Already a git repo."; exit 1; fi
git init -b main
git add .
git commit -m "chore: initial DataLens project scaffold"
echo "Run: git remote add origin <url> && git push -u origin main"
