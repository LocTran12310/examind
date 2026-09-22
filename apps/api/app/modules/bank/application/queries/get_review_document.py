from dataclasses import dataclass
import uuid

from app.modules.bank.application.dto import ReviewDocumentView
from app.modules.bank.application.ports import ReviewReader
from app.shared.application.actor import Actor
from app.shared.domain.errors import NotFound


@dataclass(frozen=True)
class GetReviewDocument:
    document_id: uuid.UUID


class GetReviewDocumentHandler:
    def __init__(self, reader: ReviewReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: GetReviewDocument) -> ReviewDocumentView:
        row = self.reader.document(actor.org_id, query.document_id)
        if row is None:
            raise NotFound("Không tìm thấy tài liệu")
        return row
