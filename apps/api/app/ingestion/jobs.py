"""Job handlers registered with the worker queue."""
from app.ingestion import extractors, pipeline  # noqa: F401  (extractors register themselves)
from app.worker.queue import FAILURE_HOOKS, handler


@handler("ingest_document")
def ingest_document(db, payload: dict) -> None:
    pipeline.ingest(db, payload["document_id"])


FAILURE_HOOKS["ingest_document"] = lambda db, payload, error: pipeline.mark_failed(db, payload["document_id"], error)
