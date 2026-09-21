"""Job handlers registered with the worker queue."""
from app.ingestion import ai_split, extractors, pipeline, topic_suggest  # noqa: F401  (stages register themselves)
from app.services.triage import triage_hook
from app.worker.queue import FAILURE_HOOKS, handler

# triage first: it fills search_text that topic suggestion (kNN) reads
if triage_hook not in pipeline.POST_PERSIST:
    pipeline.POST_PERSIST.insert(0, triage_hook)


@handler("ingest_document")
def ingest_document(db, payload: dict) -> None:
    pipeline.ingest(db, payload["document_id"])


FAILURE_HOOKS["ingest_document"] = lambda db, payload, error: pipeline.mark_failed(db, payload["document_id"], error)
