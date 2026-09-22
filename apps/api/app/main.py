from fastapi import APIRouter, FastAPI
from sqlalchemy import text

from app.core import db as dbmod, storage
from app.core.config import get_settings
from app.core.logging import setup as setup_logging

setup_logging(get_settings().log_level)

app = FastAPI(title="Examind API", docs_url="/api/docs", openapi_url="/api/openapi.json")
from app.deps import actor_from_request  # noqa: E402
from app.shared.interface import errors, request_id  # noqa: E402
from app.shared.interface.auth import register_actor_resolver  # noqa: E402

errors.install(app)
request_id.install(app)
register_actor_resolver(actor_from_request)

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


# each migrated module exposes app.modules.<context>.interface.router:router
MODULES: list[str] = ["taxonomy", "academic"]


def include_routers() -> None:
    import importlib

    from app import routers

    for name in MODULES:
        api.include_router(importlib.import_module(f"app.modules.{name}.interface.router").router)
    for r in routers.all_routers():
        api.include_router(r)


include_routers()
app.include_router(api)
