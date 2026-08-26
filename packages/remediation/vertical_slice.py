from __future__ import annotations
from pathlib import Path
import shutil
import subprocess

from packages.context.extractor import ContextExtractor
from packages.ai.patch_generator import PatchGenerator
from packages.patching.llm_adapter import SafePatchApplier
from packages.evidence.bundle import EvidenceBuilder
from packages.execution.runner import SandboxCommandRunner
from packages.sandbox.runner import SandboxRunner


class VerticalSlice:
    def __init__(self, model, max_attempts=2, runner_factory=None):
        self.generator = PatchGenerator(model)
        self.max_attempts = max_attempts
        self.runner_factory = runner_factory

    def run(self, repository: Path, finding: dict, job_id="local-e2e"):
        repository = Path(repository)
        errors = []

        for attempt in range(1, self.max_attempts + 1):
            try:
                # 1. Context
                context = ContextExtractor(repository).extract(finding)

                # 2. Model proposal
                proposal = self.generator.generate(finding, context)

                # 3. Capture baseline before touching source.
                baseline_runner = self._runner(repository)
                baseline_tests = baseline_runner.run_tests()
                baseline = {
                    "exploit_reproduced": baseline_tests.exit_code != 0,
                    "exit_code": baseline_tests.exit_code,
                    "stdout": baseline_tests.stdout,
                    "stderr": baseline_tests.stderr,
                    "argv": list(baseline_tests.argv),
                }

                # 4. Apply model diff safely.
                changed = SafePatchApplier().apply(repository, proposal)

                # 5. Run patched tests.
                patched_runner = self._runner(repository)
                patched_tests = patched_runner.run_tests()
                patched = {
                    "exploit_reproduced": patched_tests.exit_code != 0,
                    "exit_code": patched_tests.exit_code,
                    "stdout": patched_tests.stdout,
                    "stderr": patched_tests.stderr,
                    "argv": list(patched_tests.argv),
                }
                tests = {
                    "passed": patched_tests.exit_code == 0,
                    "exit_code": patched_tests.exit_code,
                    "stdout": patched_tests.stdout,
                    "stderr": patched_tests.stderr,
                    "argv": list(patched_tests.argv),
                }

                # 6. Rescan after patch. If semgrep isn't installed, fail closed.
                semgrep = patched_runner.run_semgrep()
                if semgrep["finding_count"] < 0:
                    semgrep = dict(semgrep)
                    semgrep["finding_count"] = 1
                    semgrep["error"] = "Semgrep unavailable or returned invalid JSON"

                patch = {
                    "explanation": proposal.explanation,
                    "diff": proposal.diff,
                    "changed_files": list(changed),
                }

                # 7. Evidence is the sole verification decision.
                bundle = EvidenceBuilder().build(
                    job_id=job_id,
                    finding=finding,
                    patch=patch,
                    baseline=baseline,
                    patched=patched,
                    tests=tests,
                    semgrep=semgrep,
                )
                if bundle.verified:
                    return bundle

                errors.append(f"attempt {attempt}: evidence gate failed")
                self._reset(repository)
            except Exception as exc:
                errors.append(f"attempt {attempt}: {exc}")
                self._reset(repository)

        raise RuntimeError("; ".join(errors))

    def _runner(self, repository):
        if self.runner_factory:
            return self.runner_factory(repository)
        return SandboxRunner(repository)

    @staticmethod
    def _reset(repository):
        subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=repository,
                       capture_output=True, text=True, check=False)
        subprocess.run(["git", "clean", "-fd"], cwd=repository,
                       capture_output=True, text=True, check=False)
