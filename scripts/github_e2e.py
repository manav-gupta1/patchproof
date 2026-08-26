from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.integrations.github import GitHubClient


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    repository = os.environ.get("PATCHPROOF_TEST_REPOSITORY")
    base = os.environ.get("PATCHPROOF_TEST_BASE", "main")

    if not token or not repository:
        print("SKIP: set GITHUB_TOKEN and PATCHPROOF_TEST_REPOSITORY for live GitHub E2E")
        return 0

    finding = {
        "rule_id": "patchproof.sql-concat",
        "path": "app.py",
        "start_line": 9,
        "end_line": 9,
        "fingerprint": "patchproof.sql-concat",
    }
    patch = {
        "model_provider": "fixture-replay",
        "model_name": "known-good",
        "patch_id": "fixture-sql-parameterization",
    }
    verification = {
        "verified": True,
        "baseline_reproduced": True,
        "patched_blocked": True,
        "tests_passed": True,
        "semgrep_clean": True,
        "semgrep_finding_count": 0,
    }

    # Dry-run by default. A real PR requires explicit opt-in.
    if os.environ.get("PATCHPROOF_CREATE_PR") != "1":
        print(json.dumps({
            "mode": "dry-run",
            "repository": repository,
            "base": base,
            "finding": finding,
            "patch": patch,
            "verification": verification,
        }, indent=2))
        return 0

    branch = "patchproof/e2e-sql-injection"
    sha = os.environ.get("PATCHPROOF_TEST_SHA")
    if not sha:
        print("PATCHPROOF_TEST_SHA required when PATCHPROOF_CREATE_PR=1", file=sys.stderr)
        return 2

    client = GitHubClient(token)
    client.create_branch(repository, branch, sha)

    body = """## PatchProof remediation

Verified fixture remediation.

- baseline exploit: reproduced
- patched exploit: blocked
- tests: passed
- Semgrep: clean

PatchProof verification is based on executable evidence, not model confidence.
"""
    pr = client.create_pull_request(
        repository=repository,
        title="[PatchProof] Fix verified security finding",
        head=branch,
        base=base,
        body=body,
    )
    print(json.dumps({
        "mode": "live",
        "pull_request": pr.get("html_url"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
