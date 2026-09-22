from dataclasses import dataclass
import uuid

from app.modules.bank.application.dto import ReviewDocumentView
from app.modules.bank.application.ports import ReviewReader
from app.modules.bank.domain.ports import ReviewDocuments, StaffDirectory
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Forbidden, Invalid, NotFound


@dataclass(frozen=True)
class AssignReviewer:
    document_id: uuid.UUID
    user_id: uuid.UUID | None  # None = unassign


class AssignReviewerHandler:
    """The org admin gives a document to a teacher of the centre to review."""

    def __init__(self, documents: ReviewDocuments, staff: StaffDirectory, reader: ReviewReader, uow: UnitOfWork):
        self.documents, self.staff, self.reader, self.uow = documents, staff, reader, uow

    def __call__(self, actor: Actor, cmd: AssignReviewer) -> ReviewDocumentView:
        if actor.role != "org_admin":
            raise Forbidden()
        if not self.documents.exists(actor.org_id, cmd.document_id):
            raise NotFound("Không tìm thấy tài liệu")
        if cmd.user_id is not None and not self.staff.is_teacher(actor.org_id, cmd.user_id):
            raise Invalid("Chỉ giao cho giáo viên của trung tâm", "assigned_to")
        self.documents.assign(actor.org_id, cmd.document_id, cmd.user_id)
        self.uow.commit()
        return self.reader.document(actor.org_id, cmd.document_id)
