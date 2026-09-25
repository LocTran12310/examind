from dataclasses import dataclass, field
import uuid

from app.modules.analytics.application.dto import FactScope, ReportFilters
from app.modules.analytics.application.ports import ReportReader
from app.modules.analytics.domain.services.reports import UNCLASSIFIED, ratio
from app.shared.application.actor import Actor


@dataclass(frozen=True)
class TopicStats:
    filters: ReportFilters = field(default_factory=ReportFilters)
    subject_id: uuid.UUID | None = None


class TopicStatsHandler:
    """Points over max points per topic, summed up the tree (a topic counts every fact in its subtree), by path; the
    facts without a topic as a last "Chưa phân loại" row."""

    def __init__(self, reader: ReportReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: TopicStats) -> list[dict]:
        scope = FactScope.of(actor, query.filters)
        out = [{**r, "ratio": ratio(r["points"], r["max_points"])} for r in self.reader.topics(scope, query.subject_id)]
        unc = self.reader.unclassified(scope)
        if unc["n"]:
            out.append({"id": None, "parent_id": None, "name": UNCLASSIFIED, "path": "", "depth": 1, "level_kind": "strand",
                        "subject_id": None,  # it has no topic, so it has no subject either — the row must not claim one
                        "points": unc["p"], "max_points": unc["m"], "answered": unc["n"], "ratio": ratio(unc["p"], unc["m"])})
        return out
