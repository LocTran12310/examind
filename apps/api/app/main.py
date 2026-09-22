from fastapi import APIRouter, FastAPI
from sqlalchemy import text

from app.shared.infrastructure import db as dbmod, storage
from app.shared.infrastructure.config import get_settings
from app.shared.infrastructure.logging import setup as setup_logging

setup_logging(get_settings().log_level)

app = FastAPI(title="Examind API", docs_url="/api/docs", openapi_url="/api/openapi.json")
from app.modules.academic.interface.deps import academic_api  # noqa: E402
from app.modules.analytics.infrastructure.adapters.assessment import AssessmentExams  # noqa: E402
from app.modules.analytics.infrastructure.adapters.roster import AcademicRoster as AnalyticsRoster  # noqa: E402
from app.modules.analytics.interface import deps as analytics_deps  # noqa: E402
from app.modules.assessment.infrastructure.adapters.analytics import AnalyticsFactListener  # noqa: E402
from app.modules.assessment.infrastructure.adapters.bank import BankQuestions  # noqa: E402
from app.modules.assessment.infrastructure.adapters.roster import AcademicRoster  # noqa: E402
from app.modules.assessment.infrastructure.adapters.subjects import TaxonomySubjects  # noqa: E402
from app.modules.assessment.interface import deps as assessment_deps  # noqa: E402
from app.modules.bank.infrastructure.adapters.staff import IdentityStaffDirectory  # noqa: E402
from app.modules.bank.infrastructure.adapters.taxonomy import TaxonomyAdapter  # noqa: E402
from app.modules.bank.infrastructure.repositories import IN_USE_CHECKS  # noqa: E402
from app.modules.bank.interface import deps as bank_deps  # noqa: E402
from app.modules.identity.infrastructure.adapters.classes import AcademicClassDirectory  # noqa: E402
from app.modules.identity.interface import deps as identity_deps  # noqa: E402
from app.modules.ingestion.infrastructure.adapters.assessment import AssessmentExamDrafts  # noqa: E402
from app.modules.ingestion.infrastructure.adapters.bank import BankAdapter  # noqa: E402
from app.modules.ingestion.interface import deps as ingestion_deps  # noqa: E402
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
# ingestion stores parsed questions in the bank, source tags in the taxonomy, and drafts exams through assessment;
# the worker wires the same for its jobs (app/worker/handlers.py)
ingestion_deps.register_bank(lambda db: BankAdapter(bank_deps.bank_api(db)))
ingestion_deps.register_source_tags(taxonomy_api)
ingestion_deps.register_exam_drafts(lambda db: AssessmentExamDrafts(assessment_deps.assessment_api(db)))
# assessment draws and shows questions through the bank, targets classes (academic) and students (identity), checks
# subjects (taxonomy) and tells analytics (topic mastery) about every answer fact; the bank keeps a question an exam uses
assessment_deps.register_bank(lambda db: BankQuestions(bank_deps.bank_api(db)))
assessment_deps.register_roster(lambda db: AcademicRoster(academic_api(db), identity_deps.identity_api(db)))
assessment_deps.register_subjects(lambda db: TaxonomySubjects(taxonomy_api(db)))
assessment_deps.register_fact_listener(lambda db: AnalyticsFactListener(analytics_deps.analytics_api(db)))
IN_USE_CHECKS.append(lambda db, question_id: assessment_deps.assessment_api(db).question_in_use(question_id))
# analytics lists classes (academic) and members (identity), and builds personal review exams through assessment
analytics_deps.register_roster(lambda db: AnalyticsRoster(db, academic_api(db), identity_deps.identity_api(db)))
analytics_deps.register_assessment(lambda db: AssessmentExams(assessment_deps.assessment_api(db)))

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


# each module exposes app.modules.<context>.interface.router:router
MODULES: list[str] = ["taxonomy", "academic", "identity", "bank", "ingestion", "assessment", "analytics", "audit"]


def include_routers() -> None:
    import importlib

    for name in MODULES:
        api.include_router(importlib.import_module(f"app.modules.{name}.interface.router").router)


include_routers()
app.include_router(api)
