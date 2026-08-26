from __future__ import annotations

import os
from enum import Enum
from pathlib import Path, PurePosixPath
from pydantic import BaseModel, Field, field_validator, model_validator


class PatchDecision(str, Enum):
    PATCH = "patch"
    NO_PATCH = "no_patch"


def validate_safe_relative_path(path_str: str) -> str:
    """Ensure path is safe, relative, and does not perform directory traversal."""
    if not path_str or not path_str.strip():
        raise ValueError("File path cannot be empty")
    cleaned = path_str.strip().replace("\\", "/")
    if cleaned.startswith("/") or cleaned.startswith("~"):
        raise ValueError(f"Absolute file paths are forbidden: {path_str}")
    if "\0" in cleaned:
        raise ValueError("Null bytes in path are forbidden")
    parts = cleaned.split("/")
    if any(p in ("..", ".") for p in parts if p):
        raise ValueError(f"Path traversal ('..') is forbidden: {path_str}")
    return cleaned


class FindingContext(BaseModel):
    fingerprint: str
    rule_id: str
    path: str
    start_line: int
    end_line: int
    severity: str
    source_excerpt: str
    related_symbols: list[str] = Field(default_factory=list)
    project_files: list[str] = Field(default_factory=list)


class PatchOperation(BaseModel):
    file: str
    old_text: str
    new_text: str
    reason: str = ""

    @field_validator("file")
    @classmethod
    def check_file_path(cls, v: str) -> str:
        return validate_safe_relative_path(v)

    @field_validator("old_text")
    @classmethod
    def check_old_text(cls, v: str) -> str:
        if not v:
            raise ValueError("Patch operation old_text cannot be empty")
        return v


class PatchCandidate(BaseModel):
    decision: PatchDecision = PatchDecision.PATCH
    title: str = ""
    explanation: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    operations: list[PatchOperation] = Field(default_factory=list)
    files: dict[str, str] = Field(default_factory=dict)
    changed_files: list[str] = Field(default_factory=list)
    model_provider: str = "unknown"
    model_name: str = "unknown"
    patch_id: str = ""
    finding_fingerprint: str = ""
    rationale: str = ""
    expected_security_effect: str = ""
    expected_verification_intent: str = ""

    @field_validator("changed_files")
    @classmethod
    def check_changed_files(cls, v: list[str]) -> list[str]:
        for f in v:
            validate_safe_relative_path(f)
        return v

    @field_validator("files")
    @classmethod
    def check_files_keys(cls, v: dict[str, str]) -> dict[str, str]:
        for f in v:
            validate_safe_relative_path(f)
        return v

    @model_validator(mode="after")
    def validate_patch_consistency(self) -> "PatchCandidate":
        if self.decision == PatchDecision.PATCH:
            if not self.operations and not self.files:
                raise ValueError("Patch candidate with decision=patch must contain operations or files")
            if not self.changed_files:
                if self.operations:
                    self.changed_files = list(dict.fromkeys(op.file for op in self.operations))
                elif self.files:
                    self.changed_files = list(self.files.keys())
        return self
