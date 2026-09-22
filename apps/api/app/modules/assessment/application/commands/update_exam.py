from dataclasses import dataclass, field
import uuid

from app.modules.assessment.application.common import exam_rows, load_exam
from app.modules.assessment.domain.ports import ExamRepository, QuestionBank
from app.modules.assessment.domain.services import exam_rules
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class UpdateExam:
    exam_id: uuid.UUID
    changes: dict = field(default_factory=dict)  # title, subject_id, grade, description, settings (only those sent)


class UpdateExamHandler:
    """New points per type apply to every question of that type (a teacher's own points are overwritten)."""

    def __init__(self, exams: ExamRepository, bank: QuestionBank, uow: UnitOfWork):
        self.exams, self.bank, self.uow = exams, bank, uow

    def __call__(self, actor: Actor, cmd: UpdateExam) -> None:
        e = load_exam(self.exams, actor.org_id, cmd.exam_id)
        changes = cmd.changes
        if changes.get("title") is not None:
            e.title = exam_rules.title_of(changes["title"])
        if changes.get("description") is not None:
            e.description = changes["description"]
        for f in ("grade", "subject_id"):
            if changes.get(f) is not None:
                setattr(e, f, changes[f] or None)
        if changes.get("settings") is not None:
            e.settings = exam_rules.merged_settings(e.settings, changes["settings"])
            for eq, q in exam_rows(self.exams, self.bank, e.id):
                eq.points = e.points_for(q.type)
        self.uow.commit()
