from dataclasses import dataclass
import uuid

from app.modules.bank.application.dto import QuestionView
from app.modules.bank.application.ports import QuestionViews, ReviewReader
from app.modules.bank.domain.ports import ReviewDocuments
from app.modules.bank.domain.services.review import check_question_state, group_of, waits_for_review
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest
from app.shared.domain.errors import NotFound


@dataclass(frozen=True)
class SearchDocumentQuestions:
    document_id: uuid.UUID
    request: SearchRequest
    state: str = "pending"  # pending | approved | rejected | duplicate | all


class SearchDocumentQuestionsHandler:
    """The questions of one document by review state (review-ux ADR-02): what still waits (the default, what the
    keyboard queue works on), what was approved, rejected or marked duplicate, or everything. A question that still
    waits carries its queue group, so a row can say why."""

    def __init__(self, documents: ReviewDocuments, reader: ReviewReader, views: QuestionViews):
        self.documents, self.reader, self.views = documents, reader, views

    def __call__(self, actor: Actor, query: SearchDocumentQuestions) -> Page[QuestionView]:
        state = check_question_state(query.state)
        if not self.documents.exists(actor.org_id, query.document_id):
            raise NotFound("Không tìm thấy tài liệu")
        page = self.reader.document_questions(actor.org_id, query.document_id, state, query.request)
        groups = {q.id: group_of(q) for q in page.data if waits_for_review(q)}
        return Page(self.views.views(page.data, groups), page.total, page.page, page.limit)
