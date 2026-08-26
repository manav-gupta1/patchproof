from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from packages.scanner.models import FindingLocation, NormalizedFinding


class SemgrepPayloadError(ValueError):
    """Raised when a Semgrep payload cannot be normalized safely."""


class SemgrepAdapter:
    """Normalize Semgrep's JSON schema into PatchProof's internal finding model."""

    def parse(self, payload: dict[str, Any]) -> list[NormalizedFinding]:
        results = payload.get("results")
        if not isinstance(results, list):
            raise SemgrepPayloadError("Semgrep payload must contain a 'results' array")

        findings: list[NormalizedFinding] = []
        for result in results:
            if not isinstance(result, dict):
                raise SemgrepPayloadError("Each Semgrep result must be an object")
            findings.append(self._normalize_result(result))
        return findings

    def _normalize_result(self, result: dict[str, Any]) -> NormalizedFinding:
        check_id = self._required_string(result, "check_id")
        path = self._required_string(result, "path")
        start = result.get("start")
        end = result.get("end") or start
        if not isinstance(start, dict):
            raise SemgrepPayloadError("Semgrep result is missing a valid 'start' location")

        start_line = self._required_int(start, "line")
        end_line = self._optional_int(end, "line") if isinstance(end, dict) else start_line
        start_column = self._optional_int(start, "col")
        end_column = self._optional_int(end, "col") if isinstance(end, dict) else None

        extra = result.get("extra")
        if not isinstance(extra, dict):
            extra = {}

        message = extra.get("message") or check_id
        severity = str(extra.get("severity") or "INFO").upper()
        metadata = extra.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}

        fingerprint = self._fingerprint(result, check_id, path, start_line)
        return NormalizedFinding(
            fingerprint=fingerprint,
            rule_id=check_id,
            severity=severity,
            message=str(message),
            language=self._language(result, metadata),
            location=FindingLocation(
                file=path,
                start_line=start_line,
                start_column=start_column,
                end_line=end_line,
                end_column=end_column,
            ),
            metadata=metadata,
            raw=result,
            received_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _language(result: dict[str, Any], metadata: dict[str, Any]) -> str:
        languages = metadata.get("technology") or metadata.get("languages")
        if isinstance(languages, list) and languages:
            return str(languages[0]).lower()
        if isinstance(languages, str):
            return languages.lower()
        return str(result.get("language") or "unknown").lower()

    @staticmethod
    def _fingerprint(result: dict[str, Any], rule_id: str, path: str, line: int) -> str:
        supplied = result.get("fingerprint")
        if isinstance(supplied, str) and supplied:
            return supplied
        digest = hashlib.sha256(f"{rule_id}:{path}:{line}".encode()).hexdigest()
        return digest[:32]

    @staticmethod
    def _required_string(value: dict[str, Any], key: str) -> str:
        item = value.get(key)
        if not isinstance(item, str) or not item:
            raise SemgrepPayloadError(f"Semgrep result is missing '{key}'")
        return item

    @staticmethod
    def _required_int(value: dict[str, Any], key: str) -> int:
        item = value.get(key)
        if not isinstance(item, int) or item < 1:
            raise SemgrepPayloadError(f"Semgrep location is missing valid '{key}'")
        return item

    @staticmethod
    def _optional_int(value: dict[str, Any], key: str) -> int | None:
        item = value.get(key)
        return item if isinstance(item, int) and item >= 1 else None
