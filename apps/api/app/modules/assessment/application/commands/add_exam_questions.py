from dataclasses import dataclass, field
import uuid

from app.modules.assessment.application.common import guard_edit, load_exam
from app.modules.assessment.domain.entities import ExamQuestion
from app.modules.assessment.domain.ports import ExamRepository, QuestionBank
from app.modules.assessment.domain.services import exam_rules
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Invalid


@dataclass(frozen=True)
class AddExamQuestions:
    exam_id: uuid.UUID
    question_ids: list[uuid.UUID] = field(default_factory=list)


class AddExamQuestionsHandler:
    """Approved questions of the org, appended then numbered by section; those already in the exam are skipped."""

    def __init__(self, exams: ExamRepository, bank: QuestionBank, uow: UnitOfWork):
        self.exams, self.bank, self.uow = exams, bank, uow

    def __call__(self, actor: Actor, cmd: AddExamQuestions) -> int:
        exam = load_exam(self.exams, actor.org_id, cmd.exam_id)
        guard_edit(self.exams, exam)
        existing = {eq.question_id for eq in self.exams.questions(exam.id)}
        refs = {q.id: q for q in self.bank.questions(actor.org_id, list(cmd.question_ids))}
        position, added = len(existing), 0
        for qid in cmd.question_ids:
            q = refs.get(qid)
            if q is None or not q.usable:
                raise Invalid("Chỉ thêm được câu đã duyệt của trung tâm", "question_ids")
            if q.id in existing:
                continue
            position += 1
            self.exams.add_question(ExamQuestion(exam_id=exam.id, question_id=q.id, position=position,
                                                 section=exam_rules.section_of(q.type), points=exam.points_for(q.type)))
            existing.add(q.id)
            added += 1
        exam_rules.renumbered(self.exams.questions(exam.id))
        self.uow.commit()
        return added
