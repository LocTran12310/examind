from dataclasses import dataclass
import uuid

from app.modules.assessment.domain.entities import DEFAULT_POINTS, SECTION_OF_TYPE, SECTION_ORDER, Exam, ExamQuestion
from app.modules.assessment.domain.ports import ExamRepository, QuestionBank
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class CreatePersonalExam:
    organization_id: uuid.UUID
    title: str
    created_by: uuid.UUID | None
    adaptive: dict  # the plan analytics chose: {student_id, note, plan: [{question_id, reason, topic}]}
    question_ids: tuple[uuid.UUID, ...]  # in plan order
    #: the subject the plan was drawn inside, when it was drawn inside one — a fact at build time, not a guess
    subject_id: uuid.UUID | None = None


class CreatePersonalExamHandler:
    """A personal review exam (source adaptive, THPT points): the plan's questions by section (PHẦN I → IV), each in
    plan order within its section; flushed with the caller's transaction."""

    def __init__(self, exams: ExamRepository, bank: QuestionBank, uow: UnitOfWork):
        self.exams, self.bank, self.uow = exams, bank, uow

    def __call__(self, cmd: CreatePersonalExam) -> uuid.UUID:
        exam = Exam(organization_id=cmd.organization_id, title=cmd.title, source="adaptive", created_by=cmd.created_by,
                    subject_id=cmd.subject_id,
                    settings={"points_by_type": dict(DEFAULT_POINTS), "scale_to": 10, "adaptive": cmd.adaptive})
        self.exams.add(exam)
        types = {q.id: q.type for q in self.bank.questions(None, list(cmd.question_ids))}
        order = sorted(cmd.question_ids, key=lambda i: SECTION_ORDER.index(SECTION_OF_TYPE.get(types[i], "I")))
        for position, qid in enumerate(order, start=1):
            self.exams.add_question(ExamQuestion(exam_id=exam.id, question_id=qid, position=position,
                                                 section=SECTION_OF_TYPE.get(types[qid], "I"), points=exam.points_for(types[qid])))
        self.uow.flush()
        return exam.id
