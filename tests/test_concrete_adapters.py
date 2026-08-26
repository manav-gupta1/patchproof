from pathlib import Path
import pytest

from packages.context.treesitter import TreeSitterContext
from packages.patching.apply import PatchApplier
from packages.llm.router import LLMRouter
from packages.jobs.concrete_pipeline import ConcretePipeline


def test_context_rejects_path_traversal(tmp_path):
    outside = tmp_path.parent / "secret.txt"
    outside.write_text("secret")
    with pytest.raises(ValueError):
        TreeSitterContext().extract(tmp_path, {"path": "../secret.txt"})


def test_context_is_bounded(tmp_path):
    f = tmp_path / "x.py"
    f.write_text("x = 1\n" * 10000)
    result = TreeSitterContext(max_bytes=100).extract(tmp_path, {"path": "x.py"})
    assert len(result["source"].encode()) <= 100


def test_llm_router_accepts_structured_json():
    router = LLMRouter(
        triage=lambda x: {"relevant": True},
        reasoning=lambda x: '{"patch": "diff --git a/x b/x\\n"}',
    )
    assert router.triage_finding({})["relevant"] is True
    assert "patch" in router.generate_patch({}, {})


def test_patch_applier_applies_unified_diff(tmp_path):
    subprocess = __import__("subprocess")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    f = tmp_path / "x.py"
    f.write_text("value = 1\n")
    subprocess.run(["git", "add", "x.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    patch = """diff --git a/x.py b/x.py
index 3f6c5c8..0000000 100644
--- a/x.py
+++ b/x.py
@@ -1 +1 @@
-value = 1
+value = 2
"""
    result = PatchApplier().apply(tmp_path, {"patch": patch})
    assert "value = 2" in f.read_text()
