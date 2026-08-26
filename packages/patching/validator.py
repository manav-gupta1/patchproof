from __future__ import annotations

from packages.patching.parser import UnifiedDiffParser


class PatchValidator:
    def __init__(self, repo):
        self.repo = repo
        self.parser = UnifiedDiffParser()

    def validate(self, proposal) -> None:
        proposal.validate_shape()
        self.parser.validate(proposal.diff)

        actual_files = self.parser.changed_files(proposal.diff)
        declared = set(proposal.changed_files)
        actual = set(actual_files)

        if actual != declared:
            raise ValueError(
                f"declared files {sorted(declared)} do not match diff files {sorted(actual)}"
            )

        for path in actual_files:
            self.repo.validate_relative_path(path)

        if len(actual_files) > 20:
            raise ValueError("patch touches too many files")

    def apply(self, proposal) -> None:
        self.validate(proposal)
        import subprocess
        subprocess.run(
            ["git", "-C", str(self.repo.root), "apply", "--check"],
            input=proposal.diff,
            text=True,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo.root), "apply", "--whitespace=error"],
            input=proposal.diff,
            text=True,
            capture_output=True,
            check=True,
        )
