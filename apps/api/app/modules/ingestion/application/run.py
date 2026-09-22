"""What one ingestion run carries between its stages: the document, warnings, the line stream, extractor counters and
the step log shown to the teacher (step name, milliseconds since the previous step, counters)."""
import time

from app.modules.ingestion.domain.entities import SourceDocument
from app.modules.ingestion.domain.services.lines import Line


class IngestRun:
    def __init__(self, doc: SourceDocument):
        self.doc = doc
        self.warnings: list[str] = []
        self.lines: list[Line] = []
        self.stats: dict = {}  # extractor counters shown in the extract step
        self.log: list[dict] = []
        self._t = time.monotonic()

    def step(self, name: str, **data) -> None:
        t = time.monotonic()
        self.log.append({"step": name, "ms": int((t - self._t) * 1000), **data})
        self._t = t
