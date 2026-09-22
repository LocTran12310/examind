# moved to app.shared.infrastructure.db; kept while the old layout is being retired
from app.shared.infrastructure.db import Base, IdMixin, TimestampMixin, configure, engine, get_db, session_factory  # noqa: F401
