from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql.base import ischema_names

from app.metadata import metadata  # every table and mapping of the app
from app.shared.infrastructure.config import get_settings
from app.shared.infrastructure.schema.taxonomy import LtreeType

ischema_names.setdefault("ltree", LtreeType)  # reflect ltree columns as the type the metadata uses

# indexes on expressions (accent-folded trigram search, case-folded tag names) exist only in the migrations: the
# metadata cannot state them, so the comparison (`alembic check`, autogenerate) leaves them out
EXPRESSION_INDEXES = {"ix_users_email_trgm", "ix_users_full_name_trgm", "ix_users_username_trgm", "uq_tags_org_group_name"}


def include_object(obj, name, type_, reflected, compare_to) -> bool:
    return not (type_ == "index" and name in EXPRESSION_INDEXES)


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
    context.configure(connection=connection, target_metadata=metadata, compare_type=True, include_object=include_object)
    with context.begin_transaction():
        context.run_migrations()


run_migrations_online()
