from dataclasses import dataclass
import uuid

from app.modules.bank.application.dto import QuestionView
from app.modules.bank.application.ports import QuestionViews
from app.modules.bank.domain.ports import QuestionRepository, ReviewDocuments
from app.modules.bank.domain.services.review import group_of, queue_order
from app.shared.application.actor import Actor
from app.shared.domain.errors import NotFound


@dataclass(frozen=True)
class ReviewQueue:
    document_id: uuid.UUID


class ReviewQueueHandler:
    """What is left to review in a document, grouped by problem (spot checks last)."""

    def __init__(self, questions: QuestionRepository, documents: ReviewDocuments, views: QuestionViews):
        self.questions, self.documents, self.views = questions, documents, views

    def __call__(self, actor: Actor, query: ReviewQueue) -> list[QuestionView]:
        if not self.documents.exists(actor.org_id, query.document_id):
            raise NotFound("Không tìm thấy tài liệu")
        qs = queue_order(self.questions.review_queue(query.document_id))
        return self.views.views(qs, {q.id: group_of(q) for q in qs})
