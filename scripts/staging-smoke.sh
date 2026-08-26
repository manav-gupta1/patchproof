#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Running application tests"
python -m pytest -q

echo "[2/4] Checking required staging variables"
: "${GITHUB_APP_ID:?GITHUB_APP_ID is required}"
: "${GITHUB_INSTALLATION_ID:?GITHUB_INSTALLATION_ID is required}"
: "${GITHUB_PRIVATE_KEY_FILE:?GITHUB_PRIVATE_KEY_FILE is required}"
test -s "$GITHUB_PRIVATE_KEY_FILE"

echo "[3/4] Checking Docker availability"
docker info >/dev/null

echo "[4/4] Staging prerequisites look valid"
echo "Next: start staging compose, send a controlled GitHub event, and inspect the job audit trail."
