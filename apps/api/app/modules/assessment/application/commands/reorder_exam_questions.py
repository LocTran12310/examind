from dataclasses import dataclass, field
import uuid

from app.modules.assessment.application.common import guard_edit, load_exam
from app.modules.assessment.domain.ports import ExamRepository
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Invalid


@dataclass(frozen=True)
class ReorderExamQuestions:
    exam_id: uuid.UUID
    question_ids: list[uuid.UUID] = field(default_factory=list)


class ReorderExamQuestionsHandler:
    """The draft's order as the teacher arranged it: exactly the exam's questions, positions 1..n."""

    def __init__(self, exams: ExamRepository, uow: UnitOfWork):
        self.exams, self.uow = exams, uow

    def __call__(self, actor: Actor, cmd: ReorderExamQuestions) -> None:
        exam = load_exam(self.exams, actor.org_id, cmd.exam_id)
        guard_edit(self.exams, exam)
        rows = {eq.question_id: eq for eq in self.exams.questions(exam.id)}
        if set(cmd.question_ids) != set(rows):
            raise Invalid("Danh sách câu không khớp đề", "question_ids")
        for i, qid in enumerate(cmd.question_ids, start=1):
            rows[qid].position = i
        self.uow.commit()
