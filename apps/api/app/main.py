from fastapi import APIRouter, FastAPI
from sqlalchemy import text

from app.core import db as dbmod, errors, storage
from app.core.config import get_settings
from app.core.logging import setup as setup_logging

setup_logging(get_settings().log_level)

app = FastAPI(title="Examind API", docs_url="/api/docs", openapi_url="/api/openapi.json")
errors.install(app)

api = APIRouter(prefix="/api")


@api.get("/health")
def health():
    try:
        with dbmod.engine().connect() as conn:
            conn.execute(text("select 1"))
        db_ok = "ok"
    except Exception:
        db_ok = "down"
    storage_ok = "ok" if storage.healthy() else "down"
    status = "ok" if db_ok == storage_ok == "ok" else "degraded"
    return {"status": status, "db": db_ok, "storage": storage_ok}


def include_routers() -> None:
    from app import routers

    for r in routers.all_routers():
        api.include_router(r)


include_routers()
app.include_router(api)
