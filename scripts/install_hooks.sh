#!/usr/bin/env bash
# Install git hooks for AgentProf.
# Run once after cloning: bash scripts/install_hooks.sh

set -euo pipefail

HOOK_SRC="scripts/pre-commit"
HOOK_DST=".git/hooks/pre-commit"

if [[ ! -f "$HOOK_SRC" ]]; then
    echo "ERROR: $HOOK_SRC not found. Run from repo root."
    exit 1
fi

cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"
echo "Installed pre-commit hook → $HOOK_DST"
echo "To test: git commit (will run tests on staged .py files)"
echo "To bypass: git commit --no-verify"
