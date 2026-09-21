import os

TEST_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://examind:examind@localhost:55442/examind_test"
)
os.environ["DATABASE_URL"] = TEST_URL
os.environ.setdefault("S3_ENDPOINT", "http://localhost:59100")
os.environ["S3_BUCKET"] = "examind-test"
os.environ["LOG_LEVEL"] = "warning"

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app.core import db as dbmod  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _recreate_database() -> None:
    url = make_url(TEST_URL)
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {url.database} WITH (FORCE)"))
        conn.execute(text(f"CREATE DATABASE {url.database}"))
    admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def _database():
    _recreate_database()
    cfg = Config(os.path.join(HERE, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(HERE, "migrations"))
    cfg.attributes["url"] = TEST_URL
    command.upgrade(cfg, "head")
    dbmod.configure(TEST_URL)
    yield


@pytest.fixture(autouse=True)
def _clean(_database):
    eng = dbmod.engine()
    with eng.begin() as conn:
        tables = conn.execute(
            text("select tablename from pg_tables where schemaname='public' and tablename <> 'alembic_version'")
        ).scalars().all()
        if tables:
            conn.execute(text("TRUNCATE " + ", ".join(f'"{t}"' for t in tables) + " RESTART IDENTITY CASCADE"))
    from app.seed.bootstrap import extra_seeders, seed_system

    with dbmod.session_factory()() as db:
        seed_system(db)
        extra_seeders(db)
        db.commit()
    yield


@pytest.fixture
def db():
    with dbmod.session_factory()() as session:
        yield session
        session.commit()


@pytest.fixture
def client():
    from app.main import app

    with TestClient(app, base_url="http://testserver") as c:
        yield c
