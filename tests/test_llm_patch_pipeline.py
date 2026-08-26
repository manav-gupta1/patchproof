import json
import subprocess
import sys
from pathlib import Path

from packages.ai.fixture_model import FixtureSQLInjectionModel
from packages.ai.patch_generator import PatchGenerator
from packages.context.extractor import ContextExtractor
from packages.patching.llm_adapter import SafePatchApplier


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "fixtures" / "sql_injection"


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)


def test_model_proposal_is_contextual_and_safely_applied(tmp_path):
    repo = tmp_path / "repo"
    import shutil
    shutil.copytree(FIXTURE, repo)
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@patchproof.local")
    git(repo, "config", "user.name", "PatchProof Test")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "baseline")

    finding = {
        "rule_id": "patchproof.python.sql-injection",
        "path": "app/db.py",
        "start_line": 4,
        "end_line": 4,
        "severity": "ERROR",
        "message": "User-controlled SQL concatenation",
    }
    context = ContextExtractor().extract(repo, finding)
    assert context.symbol == "get_user"

    proposal = PatchGenerator(FixtureSQLInjectionModel()).generate(finding, context)
    assert proposal.changed_files == ("app/db.py",)

    changed = SafePatchApplier().apply(repo, proposal)
    assert changed == ("app/db.py",)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=repo, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
