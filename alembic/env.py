from __future__ import annotations
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from packages.store.postgres import Base

config = context.config
if config.config_file_name:
    try:
        fileConfig(config.config_file_name)
    except Exception:
        pass

target_metadata = Base.metadata


def run_migrations_offline():
    url = os.environ["PATCHPROOF_DATABASE_URL"]
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = os.environ["PATCHPROOF_DATABASE_URL"]
    connectable = engine_from_config(
        section, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
