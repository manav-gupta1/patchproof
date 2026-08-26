from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


@dataclass(frozen=True)
class SemgrepFinding:
    rule_id: str
    path: str
    start_line: int
    end_line: int
    severity: str
    message: str
    fingerprint: str
    metadata: dict

    @classmethod
    def from_result(cls, result: dict) -> "SemgrepFinding":
        check = result.get("check_id") or result.get("rule_id")
        extra = result.get("extra") or {}
        path = result.get("path", "")
        start = (result.get("start") or {}).get("line", 0)
        end = (result.get("end") or {}).get("line", start)
        severity = extra.get("severity", "WARNING")
        message = extra.get("message", "")
        raw = f"{check}|{path}|{start}|{end}|{message}"
        fingerprint = hashlib.sha256(raw.encode()).hexdigest()
        return cls(check, path, start, end, severity, message, fingerprint, extra)


def parse_semgrep_json(payload: str | bytes | dict) -> list[SemgrepFinding]:
    if isinstance(payload, bytes):
        payload = payload.decode()
    data = json.loads(payload) if isinstance(payload, str) else payload
    return [SemgrepFinding.from_result(r) for r in data.get("results", [])]
