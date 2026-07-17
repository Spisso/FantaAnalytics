import os
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.analytics.fantaanalytics.settings import Settings

config = context.config
target_metadata = None
database_url = (
    os.getenv("DATABASE_URL")
    or config.attributes.get("database_url")
    or Settings.from_env().database_url
)
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

if context.is_offline_mode():
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
