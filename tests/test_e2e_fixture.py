from pathlib import Path

import pytest

from packages.agents import (
    StaticLLMProvider,
    VulnerabilityAnalysis,
)
from packages.context import RepositoryContext, SourceSpan
from packages.exploit import (
    ExploitAgent,
    ExploitPlan,
    ExploitRequest,
)
from packages.patching import PatchApplier, PatchCandidate, PatchOperation
from packages.sandbox import SandboxExecutor


FIXTURE = Path(__file__).parents[1] / "fixtures" / "vulnerable-python-app"


class FixtureSandbox(SandboxExecutor):
    """Safe test executor using the local Python interpreter.

    Production execution goes through Docker/gVisor. This fixture keeps the
    acceptance test deterministic and dependency-light while preserving the
    current SandboxExecutor.run(argv) contract.
    """

    def run(self, argv):
        import hashlib
        import os
        import subprocess
        import sys
        import time
        from packages.sandbox import SandboxResult

        # Keep fixture execution deterministic: the inner pytest invocation
        # must use the same Python environment as the outer acceptance test.
        command = list(argv)
        if command and command[0] in {"python", "python3"}:
            command = [sys.executable, *command[1:]]
        elif command and command[0] == "pytest":
            command = [sys.executable, "-m", "pytest", *command[1:]]

        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.repository)

        started = time.monotonic()
        proc = subprocess.run(
            command,
            cwd=self.repository,
            env=env,
            text=True,
            capture_output=True,
            timeout=self.policy.timeout_seconds,
            check=False,
        )
        return SandboxResult(
            argv=command,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            duration_ms=int((time.monotonic() - started) * 1000),
            timed_out=False,
            sandboxed=False,
            stdout_sha256=hashlib.sha256(proc.stdout.encode()).hexdigest(),
            stderr_sha256=hashlib.sha256(proc.stderr.encode()).hexdigest(),
        )

@pytest.mark.asyncio
async def test_python_sql_injection_end_to_end(tmp_path: Path) -> None:
    # Work on an isolated copy so this test never mutates the fixture.
    import shutil
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo)

    analysis = VulnerabilityAnalysis(
        finding_fingerprint="fixture-sqli-001",
        classification="sql_injection",
        confidence=0.99,
        eligible=True,
        source="user_id",
        sink="db.execute(query)",
        attack_hypothesis="user_id is interpolated into SQL and can alter query semantics",
        reasoning="f-string reaches sqlite execute without parameterization",
    )

    context = RepositoryContext(
        repository_root=str(repo),
        language="python",
        file="app.py",
        finding_span=SourceSpan(start_line=5, end_line=6),
        source='query = f"SELECT id, username FROM users WHERE id = {user_id}"\nreturn db.execute(query).fetchone()',
    )

    exploit_plan = ExploitPlan(
        finding_fingerprint="fixture-sqli-001",
        title="SQL injection reproduction",
        objective="demonstrate altered SQL semantics",
        steps=[
            {
                "description": "execute the supplied proof",
                "command": "python poc.py",
                "expected_evidence": "SQL_INJECTION_REPRODUCED",
            }
        ],
        success_condition="the proof exits successfully after demonstrating injected semantics",
    )

    sandbox = FixtureSandbox(repository=repo, workspace=repo, runtime="local")

    # 1. Baseline exploit must reproduce.
    baseline = sandbox.run(["python", "poc.py"])
    assert baseline.exit_code == 0
    assert "SQL_INJECTION_REPRODUCED" in baseline.stdout

    # 2. Generate and apply patch.
    patch = PatchCandidate(
        finding_fingerprint="fixture-sqli-001",
        title="Reject non-numeric user IDs before SQL construction",
        operations=[
            PatchOperation(
                file="app.py",
                old_text='query = f"SELECT id, username FROM users WHERE id = {user_id}"\n    return db.execute(query).fetchone()',
                new_text='if not user_id.isdigit():\n        raise ValueError("user_id must be numeric")\n    query = f"SELECT id, username FROM users WHERE id = {user_id}"\n    return db.execute(query).fetchone()',
                reason="Reject malformed input before it reaches SQL construction.",
            )
        ],
        rationale="Minimal behavioral guard for this fixture.",
        expected_security_effect="Injected SQL syntax is rejected before execution.",
    )

    PatchApplier().apply(repo, patch)

    # 3. Verify the patched repository through the current sandbox contract.
    exploit_after_patch = sandbox.run(["python", "poc.py"])
    tests_after_patch = sandbox.run(["pytest", "-q"])
    semgrep = shutil.which("semgrep")
    assert semgrep, (
        "Semgrep is required for the E2E security gate; install a runnable "
        "semgrep executable before running this acceptance test."
    )
    semgrep_after_patch = sandbox.run(
        [semgrep, "--config", "semgrep.yml", "--error", "app.py"]
    )

    assert exploit_after_patch.exit_code != 0
    assert tests_after_patch.exit_code == 0
    assert semgrep_after_patch.exit_code == 0
