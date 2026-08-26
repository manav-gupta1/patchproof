from __future__ import annotations


class LLMOutputGuard:
    """Reject obviously unsafe/non-structured patch proposals before apply."""

    MAX_PATCH_BYTES = 200_000

    def validate_patch(self, proposal):
        patch = proposal.get("patch") if isinstance(proposal, dict) else None
        if not isinstance(patch, str) or not patch.strip():
            raise ValueError("LLM patch proposal is empty")
        if len(patch.encode()) > self.MAX_PATCH_BYTES:
            raise ValueError("LLM patch proposal exceeds size limit")
        if "\x00" in patch:
            raise ValueError("LLM patch contains NUL byte")
        if not patch.startswith("diff --git "):
            raise ValueError("LLM output is not a unified git diff")
        return proposal
