from __future__ import annotations

from pydantic import AliasChoices, BaseModel, Field


class VerificationPlan(BaseModel):
    baseline_exploit: list[str]
    patched_exploit: list[str]
    test_command: list[str]
    semgrep_command: list[str] = Field(
        default_factory=lambda: ["semgrep", "--config", "p/security-audit", "--json", "."],
        validation_alias=AliasChoices("semgrep_command", "semgrep_config"),
    )
    finding_fingerprint: str


class VerificationReport(BaseModel):
    baseline_exit_code: int | None = None
    patched_exit_code: int | None = None
    tests_exit_code: int | None = None
    semgrep_exit_code: int | None = None
    semgrep_finding_count: int
    baseline_reproduced: bool = Field(
        validation_alias=AliasChoices("baseline_reproduced", "baseline_exploit_reproduced")
    )
    patched_blocked: bool = Field(
        validation_alias=AliasChoices("patched_blocked", "patched_exploit_blocked")
    )
    tests_passed: bool
    semgrep_clean: bool
    verified: bool
