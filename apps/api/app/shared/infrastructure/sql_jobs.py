"""Enqueue a job in the caller's transaction (the worker picks it up once the transaction commits)."""
import uuid

from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.shared.infrastructure.schema.jobs import jobs


class SqlJobQueue:
    def __init__(self, session: Session):
        self.session = session

    def enqueue(self, kind: str, payload: dict, max_attempts: int = 3) -> uuid.UUID:
        job_id = uuid.uuid4()
        self.session.flush()  # the job must follow the rows it refers to
        self.session.execute(insert(jobs).values(id=job_id, kind=kind, payload=payload, max_attempts=max_attempts))
        return job_id
