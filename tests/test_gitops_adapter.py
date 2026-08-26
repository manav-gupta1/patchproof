import subprocess
from pathlib import Path

import pytest

from packages.gitops.adapter import GitOpsAdapter, GitOpsError


def git(cwd, *args):
    return subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, check=True
    )


def make_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.name", "test")
    git(repo, "config", "user.email", "test@example.com")
    (repo / "app.py").write_text("print('vulnerable')\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "initial")
    return repo


def test_unverified_patch_cannot_promote(tmp_path):
    repo = make_repo(tmp_path)
    patch = tmp_path / "fix.diff"
    patch.write_text(
        "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-print('vulnerable')\n+print('fixed')\n"
    )
    with pytest.raises(GitOpsError):
        GitOpsAdapter(repo).prepare_verified_patch(
            verified=False, finding_id="abc", base_sha="HEAD",
            patch_file=patch
        )


def test_verified_patch_creates_branch_and_commit(tmp_path):
    repo = make_repo(tmp_path)
    base = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()
    patch = tmp_path / "fix.diff"
    patch.write_text(
        "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-print('vulnerable')\n+print('fixed')\n"
    )

    result = GitOpsAdapter(repo).prepare_verified_patch(
        verified=True, finding_id="abc123", base_sha=base, patch_file=patch
    )

    assert result.branch == "patchproof/abc123"
    assert result.commit_sha
    assert not result.pushed
    assert (repo / "app.py").read_text() == "print('fixed')\n"

    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=repo, text=True
    ).strip()
    assert branch == "patchproof/abc123"

    message = subprocess.check_output(
        ["git", "log", "-1", "--pretty=%s"], cwd=repo, text=True
    ).strip()
    assert message == "security: remediate abc123"


def test_dirty_repo_is_rejected(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "unrelated.txt").write_text("dirty")
    patch = tmp_path / "fix.diff"
    patch.write_text(
        "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-print('vulnerable')\n+print('fixed')\n"
    )
    with pytest.raises(GitOpsError):
        GitOpsAdapter(repo).prepare_verified_patch(
            verified=True, finding_id="abc", base_sha="HEAD", patch_file=patch
        )
