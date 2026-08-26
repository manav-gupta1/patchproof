import pytest
from config.staging import StagingConfig

def test_staging_config_requires_secrets(monkeypatch):
    for key in [
        "PATCHPROOF_DATABASE_URL", "PATCHPROOF_REDIS_URL",
        "GITHUB_APP_ID", "GITHUB_INSTALLATION_ID", "GITHUB_PRIVATE_KEY_PATH",
    ]:
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(RuntimeError):
        StagingConfig.from_env()

def test_staging_config_loads(monkeypatch):
    vals = {
        "PATCHPROOF_DATABASE_URL": "postgresql://x",
        "PATCHPROOF_REDIS_URL": "redis://x",
        "GITHUB_APP_ID": "1",
        "GITHUB_INSTALLATION_ID": "2",
        "GITHUB_PRIVATE_KEY_PATH": "/tmp/key",
    }
    for k, v in vals.items():
        monkeypatch.setenv(k, v)
    cfg = StagingConfig.from_env()
    assert cfg.github_installation_id == 2
    assert cfg.sandbox_runtime == "runsc"
