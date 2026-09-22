from dataclasses import dataclass
import uuid

from app.modules.bank.application.common import record
from app.modules.bank.application.dto import AnswerKeyResult
from app.modules.bank.domain.entities import Question
from app.modules.bank.domain.ports import QuestionRepository, ReviewDocuments, ReviewLog
from app.modules.bank.domain.services import answer_key
from app.modules.bank.domain.services.quality import blocking_manual, reevaluate, settle
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.clock import utcnow
from app.shared.domain.errors import NotFound


@dataclass(frozen=True)
class ApplyAnswerKey:
    document_id: uuid.UUID
    text: str


class ApplyAnswerKeyHandler:
    """A pasted answer key (A-06) fills the MCQs of a document (by part + number, else by a unique number);
    questions it makes complete are approved. Approved questions keep their answer."""

    def __init__(self, questions: QuestionRepository, documents: ReviewDocuments, log: ReviewLog, uow: UnitOfWork):
        self.questions, self.documents, self.log, self.uow = questions, documents, log, uow

    def __call__(self, actor: Actor, cmd: ApplyAnswerKey) -> AnswerKeyResult:
        if not self.documents.exists(actor.org_id, cmd.document_id):
            raise NotFound("Không tìm thấy tài liệu")
        key = answer_key.parse(cmd.text)
        qs = self.questions.of_document(cmd.document_id, type="mcq")
        by_part = {(q.part, q.number): q for q in qs}
        by_num: dict[int, list[Question]] = {}
        for q in qs:
            by_num.setdefault(q.number, []).append(q)
        applied, approved, unmatched = 0, 0, []
        now = utcnow()
        for (part, n), letter in sorted(key.items(), key=lambda kv: ((kv[0][0] or ""), kv[0][1])):
            q = by_part.get((part, n)) or (by_num.get(n, [None])[0] if len(by_num.get(n, [])) == 1 else None)
            if q is None or letter not in {o.get("label") for o in q.options or []}:
                unmatched.append(n)
                continue
            if q.status == "approved":
                continue
            before = q.snapshot()
            q.answer, q.answer_source = {"key": letter}, "manual"
            reevaluate(q)
            applied += 1
            if q.status == "needs_review" and not blocking_manual(q.issues):
                settle(q)
                q.status = "approved"
                q.mark_reviewed(actor.user_id, now)
                approved += 1
            record(self.log, actor, q, "answer", before, q.snapshot())
        self.uow.commit()
        return AnswerKeyResult(applied, approved, unmatched)
