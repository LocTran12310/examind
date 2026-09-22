from dataclasses import dataclass
import uuid

from app.modules.assessment.application.commands.create_exam import CreateExam, new_exam
from app.modules.assessment.domain.entities import ExamQuestion
from app.modules.assessment.domain.ports import ExamRepository, QuestionBank, Subjects
from app.modules.assessment.domain.services import exam_rules
from app.modules.assessment.domain.value_objects import DocumentRef
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Invalid


@dataclass(frozen=True)
class CreateExamFromDocument:
    document: DocumentRef
    title: str | None = None


class CreateExamFromDocumentHandler:
    """A draft exam with a document's usable questions in the original PHẦN / Câu order (official-exam-ingestion AC-11,
    AC-12). Flushed, not committed: ingestion's command owns the transaction."""

    def __init__(self, exams: ExamRepository, bank: QuestionBank, subjects: Subjects, uow: UnitOfWork):
        self.exams, self.bank, self.subjects, self.uow = exams, bank, subjects, uow

    def __call__(self, actor: Actor, cmd: CreateExamFromDocument) -> dict:
        doc = cmd.document
        if doc.status != "parsed":
            raise Invalid("Tài liệu chưa tách xong", "document")
        qs = sorted(self.bank.of_document(doc.id), key=lambda q: exam_rules.part_key(q.part, q.number))
        usable = [q for q in qs if q.usable]
        if not usable:
            raise Invalid("Chưa có câu nào của tài liệu được duyệt — hãy duyệt câu trước", "document")
        meta = doc.meta or {}
        detected = meta.get("detected") or {}
        exam = new_exam(self.exams, self.subjects, actor, CreateExam(
            exam_rules.document_title(meta, doc.filename, cmd.title), subject_id=uuid.UUID(meta["subject_id"]) if meta.get("subject_id") else None,
            grade=meta.get("grade"), description=f"Tạo từ tài liệu {doc.filename}", source="document"))
        exam.settings = {**exam.settings, "source_document_id": str(doc.id),
                         **({"duration_minutes": detected["duration"]} if detected.get("duration") else {})}
        for position, q in enumerate(usable, start=1):
            self.exams.add_question(ExamQuestion(exam_id=exam.id, question_id=q.id, position=position,
                                                 section=exam_rules.section_of(q.type), points=exam.points_for(q.type)))
        exam_rules.renumbered(self.exams.questions(exam.id))
        self.uow.flush()
        return {"exam_id": exam.id, "added": len(usable), "skipped": len(qs) - len(usable)}
