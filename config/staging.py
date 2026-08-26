from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class StagingConfig:
    database_url: str
    redis_url: str
    github_app_id: str
    github_installation_id: int
    github_private_key_path: str
    openai_api_key: str | None
    anthropic_api_key: str | None
    sandbox_runtime: str = "runsc"

    @classmethod
    def from_env(cls):
        required = [
            "PATCHPROOF_DATABASE_URL", "PATCHPROOF_REDIS_URL",
            "GITHUB_APP_ID", "GITHUB_INSTALLATION_ID",
            "GITHUB_PRIVATE_KEY_PATH",
        ]
        missing = [x for x in required if not os.getenv(x)]
        if missing:
            raise RuntimeError("missing staging configuration: " + ", ".join(missing))
        return cls(
            database_url=os.environ["PATCHPROOF_DATABASE_URL"],
            redis_url=os.environ["PATCHPROOF_REDIS_URL"],
            github_app_id=os.environ["GITHUB_APP_ID"],
            github_installation_id=int(os.environ["GITHUB_INSTALLATION_ID"]),
            github_private_key_path=os.environ["GITHUB_PRIVATE_KEY_PATH"],
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
