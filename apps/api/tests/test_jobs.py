from datetime import timedelta
import threading

from app.shared.infrastructure import db as dbmod
from app.shared.domain.clock import utcnow as now
from app.worker.queue import Job
from app.worker import queue


def test_enqueue_claim_done(db):
    seen = []
    queue.HANDLERS["t.ok"] = lambda s, p: seen.append(p["x"])
    job = queue.enqueue(db, "t.ok", {"x": 1})
    db.commit()
    assert queue.run_one(dbmod.session_factory(), "w1") is True
    db.expire_all()
    assert db.get(Job, job.id).status == "done" and seen == [1]
    assert queue.run_one(dbmod.session_factory(), "w1") is False


def test_concurrent_claims_never_share_a_job(db):
    for i in range(20):
        queue.enqueue(db, "t.noop", {"i": i})
    db.commit()
    claimed, lock = [], threading.Lock()

    def worker(n):
        f = dbmod.session_factory()
        while True:
            with f() as s:
                j = queue.claim(s, f"w{n}")
                if j is None:
                    return
                with lock:
                    claimed.append(j.id)

    ts = [threading.Thread(target=worker, args=(n,)) for n in range(4)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(claimed) == 20 == len(set(claimed))


def test_retry_with_backoff_then_failed(db):
    failures = []

    def boom(s, p):
        raise ValueError("parser exploded")

    queue.HANDLERS["t.boom"] = boom
    queue.FAILURE_HOOKS["t.boom"] = lambda s, p, err: failures.append(err)
    job = queue.enqueue(db, "t.boom", {}, max_attempts=2)
    db.commit()
    f = dbmod.session_factory()
    queue.run_one(f, "w")
    db.expire_all()
    j = db.get(Job, job.id)
    assert j.status == "queued" and j.run_after > now() and "parser exploded" in j.error
    j.run_after = None
    db.commit()
    queue.run_one(f, "w")
    db.expire_all()
    j = db.get(Job, job.id)
    assert j.status == "failed" and j.attempts == 2
    assert failures and "ValueError" in failures[0]


def test_stale_lock_is_requeued(db):
    job = queue.enqueue(db, "t.noop", {})
    job.status, job.locked_at, job.locked_by = "running", now() - timedelta(minutes=20), "dead"
    db.commit()
    assert queue.recover_stale(db) == 1
    db.expire_all()
    assert db.get(Job, job.id).status == "queued"
