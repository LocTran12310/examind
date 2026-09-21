from alembic import context
from sqlalchemy import create_engine

from app.core.config import get_settings
from app.core.db import Base
import app.models  # noqa: F401  (register tables)

config = context.config
url = config.attributes.get("url") or get_settings().database_url


def run_migrations_online() -> None:
    connectable = config.attributes.get("connection") or create_engine(url)
    if hasattr(connectable, "connect") and not hasattr(connectable, "dialect_options"):
        with connectable.connect() as connection:
            _run(connection)
    else:
        _run(connectable)


def _run(connection) -> None:
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


run_migrations_online()
