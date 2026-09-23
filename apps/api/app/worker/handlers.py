"""Job handlers registered with the worker queue; each job type calls an application command of its module.
The modules the ingestion pipeline, the attempt sweep (grading → topic mastery), the key audit and the weekly mastery
snapshot talk to are wired here as in the API's composition root (app/main.py)."""
from app.modules.academic.interface.deps import academic_api
from app.modules.analytics.interface import deps as analytics_deps
from app.modules.assessment.infrastructure.adapters.analytics import AnalyticsFactListener
from app.modules.assessment.infrastructure.adapters.bank import BankQuestions
from app.modules.assessment.infrastructure.adapters.roster import AcademicRoster
from app.modules.assessment.infrastructure.adapters.subjects import TaxonomySubjects
from app.modules.assessment.interface import deps as assessment_deps
from app.modules.bank.interface import deps as bank_deps
from app.modules.identity.interface import deps as identity_deps
from app.modules.ingestion.application.commands.ingest_document import IngestDocument, MarkIngestFailed
from app.modules.ingestion.infrastructure.adapters.bank import BankAdapter
from app.modules.ingestion.interface import deps as ingestion_deps
from app.modules.taxonomy.interface.deps import taxonomy_api
from app.worker.queue import FAILURE_HOOKS, handler

ingestion_deps.register_bank(lambda db: BankAdapter(bank_deps.bank_api(db)))
ingestion_deps.register_source_tags(taxonomy_api)
assessment_deps.register_bank(lambda db: BankQuestions(bank_deps.bank_api(db)))
assessment_deps.register_roster(lambda db: AcademicRoster(academic_api(db), identity_deps.identity_api(db)))
assessment_deps.register_subjects(lambda db: TaxonomySubjects(taxonomy_api(db)))
assessment_deps.register_fact_listener(lambda db: AnalyticsFactListener(analytics_deps.analytics_api(db)))


@handler("ingest_document")
def ingest_document(db, payload: dict) -> None:
    ingestion_deps.ingest_document(db)(IngestDocument(payload["document_id"]))


FAILURE_HOOKS["ingest_document"] = lambda db, payload, error: ingestion_deps.mark_ingest_failed(db)(MarkIngestFailed(payload["document_id"], error))


def sweep_expired_attempts(db) -> int:
    """Abandoned attempts past their deadline are submitted (the worker commits)."""
    return assessment_deps.assessment_api(db).sweep_expired()


def audit_answer_keys(db) -> list:
    """Questions whose key the students' answers contradict are flagged (adaptive-review A-09; the worker commits)."""
    return bank_deps.bank_api(db).audit_keys()


def snapshot_mastery_week(db) -> int:
    """The weekly mastery snapshot of the business week running now (learning-telemetry A-06); rows written."""
    return analytics_deps.analytics_api(db).snapshot_mastery_week()
