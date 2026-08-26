from packages.e2e.harness import ControlledRepository


def test_controlled_repo_has_stable_commit():
    repo = ControlledRepository("value = 1\n")
    path, sha = repo.create()
    assert (path / "app.py").exists()
    assert len(sha) == 40
