"""Alembic environment configuration."""
import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Add repository root to pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.config import settings
from backend.app.database import Base
from backend.app.models import (  # noqa: F401
    account,
    tariff,
    statement,
    audit,
    reversal,
    verification,
    test_run
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Determine target URL: use config value if explicitly set and not default, otherwise use settings
custom_url = config.get_main_option("sqlalchemy.url")
target_url = os.environ.get("DATABASE_URL") or settings.DATABASE_URL
if not custom_url or custom_url.strip() in ("", "sqlite:///./bank_fee_auditor.db"):
    if target_url and not target_url.startswith("sqlite"):
        # For PostgreSQL (e.g. Render hosted DB)
        sync_url = (
            target_url.replace("postgresql+asyncpg://", "postgresql://")
            .replace("postgres://", "postgresql://")
            .replace("+asyncpg", "")
        )
    elif settings.SYNC_DATABASE_URL and not settings.SYNC_DATABASE_URL.startswith("sqlite"):
        sync_url = settings.SYNC_DATABASE_URL
    else:
        sync_url = (target_url or "").replace("+asyncpg", "").replace("+aiosqlite", "")
    config.set_main_option("sqlalchemy.url", sync_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
