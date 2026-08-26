from __future__ import annotations
import os
from alembic import command
from alembic.config import Config


def migrate_database():
    url = os.environ.get("PATCHPROOF_DATABASE_URL")
    if not url:
        raise RuntimeError("PATCHPROOF_DATABASE_URL is required")
    cfg = Config("alembic.ini")
    cfg.set_main_option("script_location", "alembic")
    command.upgrade(cfg, "head")
