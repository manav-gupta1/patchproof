from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
import json


class ModelClient(Protocol):
    def complete(self, *, system: str, user: str) -> str: ...


@dataclass(frozen=True)
class PatchProposal:
    explanation: str
    diff: str
    changed_files: tuple[str, ...]
    tests_to_run: tuple[str, ...]


SYSTEM_PROMPT = """You are PatchProof's security remediation engine.
You propose minimal, reviewable source-code patches for a confirmed Semgrep
finding. Never claim a patch is verified. Verification is performed separately.

Return JSON only:
{
  "explanation": "short explanation",
  "diff": "unified git diff",
  "changed_files": ["relative/path"],
  "tests_to_run": ["command"]
}

Rules:
- Change only files necessary to remediate the finding.
- Preserve intended behavior.
- Prefer the smallest safe fix.
- Do not weaken or delete security tests.
- Do not add dependencies unless unavoidable.
- Paths must be repository-relative.
- The diff must be directly applicable with git apply.
"""


class PatchGenerator:
    def __init__(self, model: ModelClient):
        self.model = model

    def generate(self, finding: dict, context) -> PatchProposal:
        user = json.dumps({
            "finding": finding,
            "code_context": {
                "path": context.path,
                "source": context.source,
                "start_line": context.start_line,
                "end_line": context.end_line,
                "symbol": context.symbol,
                "related_tests": list(context.related_tests),
            },
        }, indent=2)

        raw = self.model.complete(system=SYSTEM_PROMPT, user=user).strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw = "\n".join(lines).strip()
        data = json.loads(raw)

        required = ("explanation", "diff", "changed_files", "tests_to_run")
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"model response missing fields: {missing}")

        changed = tuple(data["changed_files"])
        if not changed:
            raise ValueError("model returned an empty patch")
        if any(p.startswith("/") or ".." in p.split("/") for p in changed):
            raise ValueError("model returned unsafe repository paths")

        if not data["diff"].lstrip().startswith(("diff --git", "--- ")):
            raise ValueError("model did not return a unified diff")

        return PatchProposal(
            explanation=str(data["explanation"]),
            diff=str(data["diff"]),
            changed_files=changed,
            tests_to_run=tuple(data["tests_to_run"]),
        )
