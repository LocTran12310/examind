"""Job handlers registered with the worker queue; each job type calls an application command of its module.
The modules the ingestion pipeline talks to are wired here as in the API's composition root (app/main.py)."""
from app.modules.bank.interface import deps as bank_deps
from app.modules.ingestion.application.commands.ingest_document import IngestDocument, MarkIngestFailed
from app.modules.ingestion.infrastructure.adapters.bank import BankAdapter
from app.modules.ingestion.interface import deps as ingestion_deps
from app.modules.taxonomy.interface.deps import taxonomy_api
from app.worker.queue import FAILURE_HOOKS, handler

ingestion_deps.register_bank(lambda db: BankAdapter(bank_deps.bank_api(db)))
ingestion_deps.register_source_tags(taxonomy_api)


@handler("ingest_document")
def ingest_document(db, payload: dict) -> None:
    ingestion_deps.ingest_document(db)(IngestDocument(payload["document_id"]))


FAILURE_HOOKS["ingest_document"] = lambda db, payload, error: ingestion_deps.mark_ingest_failed(db)(MarkIngestFailed(payload["document_id"], error))
