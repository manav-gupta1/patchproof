from __future__ import annotations
import json
from packages.sandbox.models import ExecutionRequest
from packages.sandbox.runner import LocalSandboxRunner
from packages.verification.models import VerificationPlan, VerificationReport

class VerificationRunner:
    def __init__(self, sandbox=None): self.sandbox=sandbox or LocalSandboxRunner()
    def run(self, workspace, plan):
        baseline=self.sandbox.run(ExecutionRequest(workspace=workspace, command=plan.baseline_exploit))
        patched=self.sandbox.run(ExecutionRequest(workspace=workspace, command=plan.patched_exploit))
        tests=self.sandbox.run(ExecutionRequest(workspace=workspace, command=plan.test_command))
        semgrep=self.sandbox.run(ExecutionRequest(workspace=workspace, command=plan.semgrep_command))
        count,target=self._semgrep_status(semgrep.stdout, plan)
        a=baseline.exit_code==0 and not baseline.timed_out
        b=patched.exit_code!=0 and not patched.timed_out
        c=tests.exit_code==0 and not tests.timed_out
        d=semgrep.exit_code==0 and not semgrep.timed_out and count==0 and not target
        return VerificationReport(baseline_exit_code=baseline.exit_code,patched_exit_code=patched.exit_code,
          tests_exit_code=tests.exit_code,semgrep_exit_code=semgrep.exit_code,semgrep_finding_count=count,
          baseline_reproduced=a,patched_blocked=b,tests_passed=c,semgrep_clean=d,verified=a and b and c and d)
    @staticmethod
    def _semgrep_status(stdout, plan):
        try: data=json.loads(stdout)
        except (json.JSONDecodeError,TypeError): return -1,True
        results=data.get("results")
        if not isinstance(results,list): return -1,True
        target=any((r.get("check_id") or r.get("checkId"))==plan.finding_fingerprint for r in results)
        return len(results),target
