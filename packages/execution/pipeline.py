from __future__ import annotations
from dataclasses import dataclass

from packages.sandbox.service import SandboxExecutionService
from packages.evidence.execution import (
    ScannerResult, TestResult, VerificationResult, build_execution_evidence
)


@dataclass(frozen=True)
class PipelineResult:
    scanner: ScannerResult
    tests: TestResult
    verification: VerificationResult
    execution_evidence: object


class RealVerificationPipeline:
    def __init__(self, repo_dir, sandbox=None):
        self.repo_dir = repo_dir
        self.sandbox = sandbox or SandboxExecutionService()

    def run(self):
        scanner = self.sandbox.execute(
            self.repo_dir, ("semgrep", "--config", "auto", "--json", ".")
        )
        scanner_result = ScannerResult(
            findings=0 if scanner.succeeded else 1,
            output=scanner.combined_output,
        )

        tests = self.sandbox.execute(
            self.repo_dir, ("python", "-m", "pytest", "-q")
        )
        test_result = TestResult(
            passed=self._passed_count(tests.stdout),
            failed=0 if tests.succeeded else 1,
            output=tests.combined_output,
        )

        verified = scanner.succeeded and tests.succeeded and scanner_result.findings == 0
        verification_output = (
            "verification passed: scanner clean and test suite passed"
            if verified else
            "verification failed: scanner or test suite did not pass"
        )
        verification_result = VerificationResult(
            verified=verified,
            output=verification_output,
        )

        evidence = build_execution_evidence(
            scanner_result, test_result, verification_result
        )
        return PipelineResult(
            scanner=scanner_result,
            tests=test_result,
            verification=verification_result,
            execution_evidence=evidence,
        )

    @staticmethod
    def _passed_count(output):
        # Pytest's final line normally contains "N passed". Keep this parser
        # deliberately conservative; the raw output is retained as evidence.
        import re
        match = re.search(r"(\d+) passed", output)
        return int(match.group(1)) if match else 0
