from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Execution:
    exploit_reproduced: bool = False


@dataclass(frozen=True)
class Tests:
    passed: bool


@dataclass(frozen=True)
class Scan:
    finding_count: int


class FixtureRunner:
    def __init__(self, *, vulnerable=True, patched=True, tests_pass=True, semgrep_findings=0):
        self.vulnerable = vulnerable
        self.patched = patched
        self.tests_pass = tests_pass
        self.semgrep_findings = semgrep_findings

    def run_baseline(self, finding):
        return Execution(self.vulnerable)

    def run_patched(self, finding, proposal):
        return Execution(self.patched)

    def run_tests(self, proposal):
        return Tests(self.tests_pass)

    def run_semgrep(self, proposal):
        return Scan(self.semgrep_findings)
