import json
from packages.verification import VerificationPlan, VerificationRunner
def test_target_finding_blocks_clean():
    n,t=VerificationRunner._semgrep_status(json.dumps({"results":[{"check_id":"patchproof.sql-concat"}]}),
        VerificationPlan(baseline_exploit=["true"],patched_exploit=["false"],test_command=["true"],finding_fingerprint="patchproof.sql-concat"))
    assert (n,t)==(1,True)
