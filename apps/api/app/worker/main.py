"""Worker entry point: `python -m app.worker.main`."""
import os
import pathlib
import signal
import socket
import threading
import time

import structlog

from app.core import db as dbmod
from app.core.config import get_settings
from app.core.logging import setup as setup_logging
from app.worker import queue

HEARTBEAT = pathlib.Path("/tmp/worker-heartbeat")
log = structlog.get_logger("worker")
stop = threading.Event()


def load_handlers() -> None:
    import app.ingestion.jobs  # noqa: F401  (registers ingest_document)


def loop(worker_id: str) -> None:
    factory = dbmod.session_factory()
    idle = 0.0
    while not stop.is_set():
        try:
            did = queue.run_one(factory, worker_id)
        except Exception as exc:  # database hiccup: back off and keep the worker alive
            log.error("worker.loop_error", error=str(exc))
            did = False
        idle = 0.0 if did else min(2.0, idle + 0.5)
        if idle:
            stop.wait(idle)


def main() -> None:
    setup_logging(get_settings().log_level)
    load_handlers()
    concurrency = int(os.environ.get("INGEST_CONCURRENCY", "1"))
    base = f"{socket.gethostname()}:{os.getpid()}"
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    threads = [threading.Thread(target=loop, args=(f"{base}:{i}",), daemon=True) for i in range(concurrency)]
    for t in threads:
        t.start()
    log.info("worker.started", concurrency=concurrency)
    factory = dbmod.session_factory()
    while not stop.is_set():
        HEARTBEAT.touch()
        with factory() as db:
            recovered = queue.recover_stale(db)
            if recovered:
                log.warning("worker.recovered_stale", count=recovered)
        stop.wait(10)
    for t in threads:
        t.join(timeout=30)


if __name__ == "__main__":
    main()
