from dataclasses import dataclass
import uuid

from app.modules.bank.application.dto import QuestionView
from app.modules.bank.application.ports import QuestionViews
from app.modules.bank.domain.ports import DocumentQuestions, ReviewDocuments
from app.shared.application.actor import Actor
from app.shared.domain.errors import NotFound


@dataclass(frozen=True)
class DocumentQuestionsQuery:
    document_id: uuid.UUID


class DocumentQuestionsHandler:
    """Every question parsed from a document, PHẦN then Câu order, with topics and tags (the document page)."""

    def __init__(self, documents: ReviewDocuments, questions: DocumentQuestions, views: QuestionViews):
        self.documents, self.questions, self.views = documents, questions, views

    def __call__(self, actor: Actor, query: DocumentQuestionsQuery) -> list[QuestionView]:
        if not self.documents.exists(actor.org_id, query.document_id):
            raise NotFound("Không tìm thấy tài liệu")
        return self.views.views(self.questions.in_order(query.document_id))
