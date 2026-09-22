from dataclasses import dataclass, field

from app.modules.analytics.application.dto import FactScope, ReportFilters
from app.modules.analytics.application.ports import ReportReader
from app.modules.analytics.domain.services.reports import check_group, ratio
from app.shared.application.actor import Actor


@dataclass(frozen=True)
class GroupStats:
    by: str = "type"  # type | difficulty | tag
    filters: ReportFilters = field(default_factory=ReportFilters)


class GroupStatsHandler:
    """Points over max points per question type, difficulty or tag, weakest first (groups without points last)."""

    def __init__(self, reader: ReportReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: GroupStats) -> list[dict]:
        check_group(query.by)
        rows = self.reader.groups(FactScope.of(actor, query.filters), query.by)
        return sorted(({"key": r["key"], "label": r["label"], "points": r["p"], "max_points": r["m"], "answered": r["n"],
                        "ratio": ratio(r["p"], r["m"])} for r in rows), key=lambda x: (x["ratio"] is None, x["ratio"]))
