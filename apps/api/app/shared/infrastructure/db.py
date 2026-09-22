from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, registry, sessionmaker

from app.shared.infrastructure.config import get_settings

# one registry and one MetaData for the whole schema: the tables live in shared/infrastructure/schema/<area>.py and
# each module maps its dataclasses onto them imperatively (architecture-refactor ADR-01)
mapper_registry = registry()
metadata = mapper_registry.metadata

_engine = None
_SessionLocal: sessionmaker | None = None


def configure(url: str | None = None) -> None:
    """(Re)bind the engine; tests call this with the test database URL."""
    global _engine, _SessionLocal
    _engine = create_engine(url or get_settings().database_url, pool_pre_ping=True)
    _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)


def engine():
    if _engine is None:
        configure()
    return _engine


def session_factory() -> sessionmaker:
    if _SessionLocal is None:
        configure()
    return _SessionLocal


def get_db() -> Iterator[Session]:
    db = session_factory()()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
