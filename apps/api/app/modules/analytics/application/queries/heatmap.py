from dataclasses import dataclass
import uuid

from app.modules.analytics.application.dto import FactScope, ReportFilters
from app.modules.analytics.application.ports import ReportReader
from app.modules.analytics.domain.services.reports import check_staff, heat_level, ratio
from app.shared.application.actor import Actor


@dataclass(frozen=True)
class Heatmap:
    class_id: uuid.UUID
    level: int = 1
    subject_id: uuid.UUID | None = None
    term_code: str | None = None


class HeatmapHandler:
    """A class × topics of one level (1–4): every active student of the class with, per topic, the ratio and the number
    of answers given while in the class (staff only)."""

    def __init__(self, reader: ReportReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: Heatmap) -> dict:
        check_staff(actor.role)
        level = heat_level(query.level)
        scope = FactScope.of(actor, ReportFilters(class_id=query.class_id, term_code=query.term_code))
        rows = self.reader.heat(scope, level, query.subject_id)
        columns = list({r["topic_id"]: {"id": r["topic_id"], "name": r["name"], "path": r["path"]} for r in rows}.values())
        cells: dict = {}
        for r in rows:
            cells.setdefault(str(r["student_id"]), {})[str(r["topic_id"])] = {"ratio": ratio(r["p"], r["m"]), "answered": r["n"]}
        members = self.reader.class_students(actor.org_id, query.class_id)
        return {"columns": columns, "rows": [{"student_id": m["id"], "full_name": m["full_name"], "username": m["username"],
                                              "cells": cells.get(str(m["id"]), {})} for m in members]}
