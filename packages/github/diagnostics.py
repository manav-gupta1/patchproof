from __future__ import annotations

import os
from typing import Any


def get_github_config_diagnostics() -> dict[str, str]:
    """Inspect configured GitHub environment variables without leaking any secret values."""
    vars_to_check = [
        "GITHUB_APP_ID",
        "GITHUB_APP_PRIVATE_KEY",
        "GITHUB_APP_PRIVATE_KEY_PATH",
        "GITHUB_APP_INSTALLATION_ID",
        "GITHUB_INSTALLATION_ID",
        "GITHUB_WEBHOOK_SECRET",
        "GITHUB_API_URL",
        "PATCHPROOF_GITHUB_INTEGRATION_TEST",
        "PATCHPROOF_TEST_REPOSITORY",
    ]

    diagnostics = {}
    for var in vars_to_check:
        val = os.environ.get(var, "").strip()
        diagnostics[var] = "configured: yes" if bool(val) else "configured: no"

    return diagnostics


def print_github_config_diagnostics() -> None:
    """Print safe GitHub configuration summary without leaking secrets."""
    diag = get_github_config_diagnostics()
    print("=== PatchProof GitHub Configuration Diagnostics ===")
    for var, status in diag.items():
        print(f"  {var}: {status}")
    print("====================================================")
