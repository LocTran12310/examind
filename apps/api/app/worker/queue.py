"""Postgres job queue (ADR-01): enqueue, claim with SKIP LOCKED, finish, retry, stale recovery."""
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import traceback
import uuid

from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from app.shared.domain.clock import utcnow as now
from app.shared.domain.ids import new_id
from app.shared.infrastructure.db import mapper_registry
from app.shared.infrastructure.schema.jobs import jobs


@dataclass(eq=False)
class Job:
    """A row of the queue (mapped onto shared.infrastructure.schema.jobs)."""
    kind: str
    payload: dict = field(default_factory=dict)
    status: str = "queued"  # queued | running | done | failed
    attempts: int = 0
    max_attempts: int = 3
    run_after: datetime | None = None
    locked_at: datetime | None = None
    locked_by: str | None = None
    error: str | None = None
    finished_at: datetime | None = None
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime | None = None


if not any(m.class_ is Job for m in mapper_registry.mappers):
    mapper_registry.map_imperatively(Job, jobs)

STALE_AFTER = timedelta(minutes=15)
HANDLERS: dict[str, Callable[[Session, dict], None]] = {}


def handler(kind: str):
    def register(fn):
        HANDLERS[kind] = fn
        return fn

    return register


def enqueue(db: Session, kind: str, payload: dict, max_attempts: int = 3) -> Job:
    job = Job(kind=kind, payload=payload, max_attempts=max_attempts)
    db.add(job)
    db.flush()
    return job


def claim(db: Session, worker_id: str) -> Job | None:
    """Atomically take the oldest runnable job; concurrent claimers skip locked rows."""
    row = db.execute(text("""
        update jobs set status = 'running', locked_at = now(), locked_by = :w, attempts = attempts + 1
         where id = (
           select id from jobs
            where status = 'queued' and (run_after is null or run_after <= now())
            order by created_at
            for update skip locked
            limit 1)
        returning id
    """), {"w": worker_id}).first()
    db.commit()
    return db.get(Job, row[0]) if row else None


def recover_stale(db: Session) -> int:
    res = db.execute(
        update(Job)
        .where(Job.status == "running", Job.locked_at < now() - STALE_AFTER)
        .values(status="queued", locked_at=None, locked_by=None)
    )
    db.commit()
    return res.rowcount or 0


def run_one(db_factory, worker_id: str) -> bool:
    """Claim and run a single job. Returns False when the queue was empty."""
    with db_factory() as db:
        job = claim(db, worker_id)
        if job is None:
            return False
        job_id, kind, payload = job.id, job.kind, dict(job.payload)
    fn = HANDLERS.get(kind)
    try:
        if fn is None:
            raise RuntimeError(f"no handler for job kind {kind!r}")
        with db_factory() as db:
            fn(db, payload)
            db.commit()
        _finish(db_factory, job_id, None)
    except Exception as exc:  # noqa: BLE001 — every failure is recorded on the job
        _finish(db_factory, job_id, f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=8)}")
    return True


def _finish(db_factory, job_id: uuid.UUID, error: str | None) -> None:
    with db_factory() as db:
        job = db.get(Job, job_id)
        if error is None:
            job.status, job.error, job.finished_at = "done", None, now()
        elif job.attempts >= job.max_attempts:
            job.status, job.error, job.finished_at = "failed", error, now()
            on_failed = FAILURE_HOOKS.get(job.kind)
            if on_failed:
                on_failed(db, job.payload, error)
        else:
            job.status, job.error = "queued", error
            job.run_after = now() + timedelta(seconds=5 * 2 ** (job.attempts - 1))
        job.locked_at = job.locked_by = None
        db.commit()


FAILURE_HOOKS: dict[str, Callable[[Session, dict, str], None]] = {}


def pending(db: Session, kind: str | None = None) -> list[Job]:
    stmt = select(Job).where(Job.status.in_(("queued", "running")))
    if kind:
        stmt = stmt.where(Job.kind == kind)
    return db.scalars(stmt).all()
