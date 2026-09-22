from dataclasses import dataclass
import uuid

from app.modules.bank.application.common import record
from app.modules.bank.domain.ports import QuestionRepository, ReviewDocuments, ReviewLog
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.clock import utcnow
from app.shared.domain.errors import NotFound


@dataclass(frozen=True)
class ApproveConfident:
    document_id: uuid.UUID


class ApproveConfidentHandler:
    """Every auto-approved question of a document that is not waiting for a spot check becomes approved."""

    def __init__(self, questions: QuestionRepository, documents: ReviewDocuments, log: ReviewLog, uow: UnitOfWork):
        self.questions, self.documents, self.log, self.uow = questions, documents, log, uow

    def __call__(self, actor: Actor, cmd: ApproveConfident) -> int:
        if not self.documents.exists(actor.org_id, cmd.document_id):
            raise NotFound("Không tìm thấy tài liệu")
        qs = self.questions.of_document(cmd.document_id, status="auto_approved", spot_check=False)
        now = utcnow()
        for q in qs:
            q.status = "approved"
            q.mark_reviewed(actor.user_id, now)
        if qs:
            record(self.log, actor, None, "bulk", {"status": "auto_approved"},
                   {"status": "approved", "count": len(qs), "document": str(cmd.document_id)})
        self.uow.commit()
        return len(qs)
