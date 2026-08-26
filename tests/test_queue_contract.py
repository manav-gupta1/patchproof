from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_durable_queue_uses_streams_and_consumer_groups():
    code = (ROOT / "packages/queue/claim.py").read_text()
    assert "xgroup_create" in code
    assert "xreadgroup" in code
    assert "xack" in code
    assert "xautoclaim" in code


def test_pipeline_is_dependency_injected():
    code = (ROOT / "packages/pipeline.py").read_text()
    for name in ["triage", "context", "patcher", "applier", "verifier", "github"]:
        assert f"self.{name}" in code


def test_worker_rejects_failed_jobs():
    code = (ROOT / "packages/queue/worker.py").read_text()
    assert "JobState.REJECTED" in code
    assert "pipeline exception" in code
