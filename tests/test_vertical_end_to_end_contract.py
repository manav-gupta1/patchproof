from pathlib import Path

from packages.patching.contracts import PatchProposal
from packages.vertical.runner import VerticalSliceRunner


class FakeContext:
    def __init__(self, value):
        self.value=value
    def as_dict(self):
        return self.value


class ContextExtractor:
    def extract(self, finding):
        return FakeContext({"code": "safe", "path": finding["path"]})


class Generator:
    def generate(self, finding, context):
        return PatchProposal(
            diff="""diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,1 +1,1 @@
-def x(): return 1
+def x(): return 2
""",
            changed_files=["app.py"],
            explanation="minimal fix",
            security_rationale="fixes finding",
            confidence=0.9,
        )


class Repo:
    def __init__(self, root):
        self.root=Path(root)
    def validate_relative_path(self, path):
        candidate=(self.root/path).resolve()
        if self.root not in candidate.parents and candidate != self.root:
            raise ValueError("escape")
        return candidate


class Validator:
    def __init__(self, repo):
        self.repo=repo


class EvidenceStore:
    def __init__(self):
        self.evidence=[]
        self.transitions=[]
    def add_evidence(self, job_id, kind, payload):
        self.evidence.append((job_id,kind,payload))
        return "evidence-1"
    def transition(self, job, *, to_state, actor, reason):
        job.state=to_state
        self.transitions.append((job.job_id,to_state,actor,reason))


class Report:
    verified=True
    def as_dict(self):
        return {"verified": True, "baseline_reproduced": True,
                "patched_blocked": True, "tests_passed": True,
                "semgrep_clean": True, "semgrep_finding_count": 0, "commands": []}


class Verification:
    def verify(self, **kwargs):
        return Report()


def test_vertical_slice_ordering(monkeypatch, tmp_path):
    import packages.vertical.runner as vr
    monkeypatch.setattr(vr, "PatchValidator", lambda repo: type(
        "V", (), {"apply": lambda self, proposal: None}
    )())

    class Job:
        job_id="job-1"
        state=type("S", (), {"value":"PATCH_APPLIED"})()

    store=EvidenceStore()
    runner=VerticalSliceRunner(
        context_extractor=ContextExtractor(),
        patch_generator=Generator(),
        patch_repository=store,
        verification_engine=Verification(),
        repository=Repo(tmp_path),
    )
    result=runner.run(
        Job(), {"path":"app.py","start_line":1,"end_line":1},
        baseline_exploit=["exploit-before"],
        patched_exploit=["exploit-after"],
        test_command=["pytest"],
    )
    assert result.verified
    assert result.final_state == "verified"
    assert result.evidence_id == "evidence-1"
    assert result.patch_files == ["app.py"]
    assert store.transitions
