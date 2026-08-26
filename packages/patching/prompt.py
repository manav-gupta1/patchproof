from __future__ import annotations

import json


SYSTEM_PROMPT = """
You are PatchProof's security remediation patcher.
Produce a minimal, reviewable security patch for the supplied Semgrep finding.
Never invent files or tests. Do not remove security checks merely to silence Semgrep.
Return structured JSON matching the PatchProposal contract.
The diff must be a valid git unified diff.
""".strip()


def build_patch_prompt(finding: dict, context: dict) -> str:
    payload = {
        "finding": finding,
        "context": context,
        "requirements": [
            "fix the reported vulnerability",
            "preserve existing behavior outside the security fix",
            "prefer the smallest safe change",
            "identify assumptions explicitly",
            "include only files actually changed by the diff",
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)
