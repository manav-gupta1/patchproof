from __future__ import annotations

from pydantic import BaseModel, Field


class SourceSpan(BaseModel):
    start_line: int
    end_line: int


class SymbolContext(BaseModel):
    name: str
    kind: str
    span: SourceSpan
    signature: str | None = None


class CallSite(BaseModel):
    name: str
    line: int
    receiver: str | None = None


class RepositoryContext(BaseModel):
    repository_root: str
    language: str
    file: str
    finding_span: SourceSpan
    source: str
    enclosing_symbol: str | None = None
    enclosing_symbol_span: SourceSpan | None = None
    imports: list[str] = Field(default_factory=list)
    symbols: list[SymbolContext] = Field(default_factory=list)
    calls: list[CallSite] = Field(default_factory=list)
    related_files: list[str] = Field(default_factory=list)
    related_tests: list[str] = Field(default_factory=list)
