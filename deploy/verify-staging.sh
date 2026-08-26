#!/usr/bin/env bash
set -euo pipefail
: "${GITHUB_APP_ID:?missing GITHUB_APP_ID}"
: "${GITHUB_INSTALLATION_ID:?missing GITHUB_INSTALLATION_ID}"
: "${GITHUB_PRIVATE_KEY_FILE:?missing GITHUB_PRIVATE_KEY_FILE}"
test -s "$GITHUB_PRIVATE_KEY_FILE"
python -m pytest -q
echo "Local test suite passed."
echo "Staging prerequisites: dedicated GitHub App/repository, webhook secret,"
echo "gVisor runsc on worker host, and deployment-managed secrets."
