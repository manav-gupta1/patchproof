from __future__ import annotations

import json
from typing import Any

from packages.patching.models import (
    FindingContext,
    PatchCandidate,
    PatchDecision,
    PatchOperation,
    validate_safe_relative_path,
)

MAX_RAW_RESPONSE_BYTES = 2_097_152  # 2MB max JSON response size


PATCH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "decision",
        "explanation",
        "patch_id",
    ],
    "properties": {
        "decision": {"type": "string", "enum": ["patch", "no_patch"]},
        "title": {"type": "string", "maxLength": 300},
        "explanation": {"type": "string", "minLength": 1, "maxLength": 8000},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "operations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["file", "old_text", "new_text"],
                "properties": {
                    "file": {"type": "string", "maxLength": 500},
                    "old_text": {"type": "string", "maxLength": 500_000},
                    "new_text": {"type": "string", "maxLength": 500_000},
                    "reason": {"type": "string", "maxLength": 1000},
                },
            },
            "maxItems": 50,
        },
        "files": {
            "type": "object",
            "additionalProperties": {"type": "string", "maxLength": 2_000_000},
            "maxProperties": 30,
        },
        "changed_files": {
            "type": "array",
            "items": {"type": "string", "maxLength": 500},
            "maxItems": 30,
        },
        "model_provider": {"type": "string", "maxLength": 200},
        "model_name": {"type": "string", "maxLength": 200},
        "patch_id": {"type": "string", "minLength": 1, "maxLength": 200},
        "finding_fingerprint": {"type": "string", "maxLength": 200},
        "rationale": {"type": "string", "maxLength": 2000},
        "expected_security_effect": {"type": "string", "maxLength": 2000},
        "expected_verification_intent": {"type": "string", "maxLength": 2000},
    },
}


def build_patch_prompt(context: FindingContext) -> str:
    return f"""You are PatchProof's security remediation engineer.

Analyze this Semgrep finding and propose the minimal, safest code patch.

RULE: {context.rule_id}
SEVERITY: {context.severity}
FINGERPRINT: {context.fingerprint}
FILE: {context.path}
LINES: {context.start_line}-{context.end_line}

SOURCE CONTEXT:
{context.source_excerpt}

NEARBY SYMBOLS:
{chr(10).join(context.related_symbols)}

PROJECT FILES:
{chr(10).join(context.project_files[:250])}

Return ONLY a JSON object strictly matching this schema:
{{
  "decision": "patch" | "no_patch",
  "title": "fix(security): brief commit title",
  "explanation": "Detailed explanation of why this fix resolves the vulnerability safely",
  "confidence": 0.95,
  "operations": [
    {{
      "file": "{context.path}",
      "old_text": "exact code snippet to replace",
      "new_text": "remediated code snippet",
      "reason": "why this replacement works"
    }}
  ],
  "changed_files": ["{context.path}"],
  "expected_verification_intent": "Vulnerability rule {context.rule_id} will be eliminated",
  "patch_id": "patch-unique-id"
}}

Rules:
1. Use "decision": "no_patch" if the finding is ambiguous, requires large architectural rewrites, or lacks context.
2. If "decision": "patch", provide exact "operations" with non-empty "old_text" matching the original source.
3. Never use absolute paths (e.g. /etc/passwd) or path traversals (../).
4. Do not wrap JSON in markdown backticks. Return raw JSON only.
"""


def parse_patch_response(
    raw: str,
    *,
    provider: str,
    model_name: str,
) -> PatchCandidate:
    if not raw or not raw.strip():
        raise ValueError("Model response is empty")

    if len(raw.encode("utf-8")) > MAX_RAW_RESPONSE_BYTES:
        raise ValueError(f"Model response exceeds maximum size limit ({MAX_RAW_RESPONSE_BYTES} bytes)")

    # Clean potential markdown backticks if model wrapped JSON
    cleaned = raw.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("model response is not valid JSON") from exc

    if not isinstance(data, dict):
        raise ValueError("model response must be a JSON object")

    # Reject unknown keys
    unknown = set(data) - set(PATCH_SCHEMA["properties"])
    if unknown:
        raise ValueError(f"unknown patch fields: {sorted(unknown)}")

    # Path traversal validation on all paths
    for f in data.get("changed_files", []):
        validate_safe_relative_path(f)
    for f in data.get("files", {}).keys():
        validate_safe_relative_path(f)
    for op in data.get("operations", []):
        if isinstance(op, dict) and "file" in op:
            validate_safe_relative_path(op["file"])
        if isinstance(op, dict) and not op.get("old_text"):
            raise ValueError("Patch operation old_text cannot be empty")

    if data.get("files") and "changed_files" in data and set(data["changed_files"]) != set(data["files"]):
        raise ValueError("changed_files must exactly match files")

    # Confidence validation
    if "confidence" in data:
        conf = float(data["confidence"])
        if not (0.0 <= conf <= 1.0):
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {conf}")

    candidate = PatchCandidate.model_validate(data)

    if candidate.model_provider == "unknown":
        candidate.model_provider = provider
    if candidate.model_name == "unknown":
        candidate.model_name = model_name

    if candidate.decision is PatchDecision.NO_PATCH and (candidate.files or candidate.operations):
        raise ValueError("no_patch candidate cannot contain files or operations")

    if candidate.decision is PatchDecision.PATCH and not candidate.files and not candidate.operations:
        raise ValueError("patch candidate must contain files or operations")

    return candidate
