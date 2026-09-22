from typing import Protocol
import uuid


class JobQueue(Protocol):
    """Background work run by the worker after the command's transaction commits (exam-ingestion ADR-01)."""

    def enqueue(self, kind: str, payload: dict, max_attempts: int = 3) -> uuid.UUID: ...
