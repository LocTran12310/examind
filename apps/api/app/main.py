from fastapi import APIRouter, FastAPI
from sqlalchemy import text

from app.core import db as dbmod, storage
from app.core.config import get_settings
from app.core.logging import setup as setup_logging

setup_logging(get_settings().log_level)

app = FastAPI(title="Examind API", docs_url="/api/docs", openapi_url="/api/openapi.json")
from app.modules.academic.interface.deps import academic_api  # noqa: E402
from app.modules.bank.infrastructure.adapters.staff import IdentityStaffDirectory  # noqa: E402
from app.modules.bank.infrastructure.adapters.taxonomy import TaxonomyAdapter  # noqa: E402
from app.modules.bank.interface import deps as bank_deps  # noqa: E402
from app.modules.identity.infrastructure.adapters.classes import AcademicClassDirectory  # noqa: E402
from app.modules.identity.interface import deps as identity_deps  # noqa: E402
from app.modules.taxonomy.interface.deps import taxonomy_api  # noqa: E402
from app.seed.org_seeder import SeedOrgSeeder  # noqa: E402
from app.shared.interface import errors, request_id  # noqa: E402
from app.shared.interface.auth import register_actor_resolver  # noqa: E402

errors.install(app)
request_id.install(app)
# identity authenticates every request; the other modules only ask for an Actor
register_actor_resolver(identity_deps.actor_from_request)
# the user import and membership removal reach the academic context's classes through its application API
identity_deps.register_class_directory(lambda db: AcademicClassDirectory(academic_api(db)))
identity_deps.register_org_seeder(SeedOrgSeeder)
# the bank checks topics / tags through the taxonomy API and reviewers through the identity API
bank_deps.register_taxonomy(lambda db: TaxonomyAdapter(taxonomy_api(db)))
bank_deps.register_staff_directory(lambda db: IdentityStaffDirectory(identity_deps.identity_api(db)))

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
MODULES: list[str] = ["taxonomy", "academic", "identity", "bank"]


def include_routers() -> None:
    import importlib

    from app import routers

    for name in MODULES:
        api.include_router(importlib.import_module(f"app.modules.{name}.interface.router").router)
    for r in routers.all_routers():
        api.include_router(r)


include_routers()
app.include_router(api)
