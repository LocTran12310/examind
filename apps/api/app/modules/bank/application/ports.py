"""Read ports of the bank (search, facets, review lists, item statistics) and the question presenter."""
from typing import Protocol
import uuid

from app.modules.bank.application.dto import ItemStats, QuestionView, ResolvedFilters, ReviewDocumentView
from app.modules.bank.domain.entities import Question
from app.shared.application.search import Page, SearchRequest


class QuestionViews(Protocol):
    def views(self, questions: list[Question], groups: dict[uuid.UUID, str] | None = None) -> list[QuestionView]:
        """Questions with their topics (primary first) and tags."""
        ...


class QuestionReader(QuestionViews, Protocol):
    def search(self, org_id: uuid.UUID, req: SearchRequest, f: ResolvedFilters) -> Page[QuestionView]:
        """Relevance first when searching text, then newest. Filters: stem (text) · created_at, updated_at (date) ·
        number, grade (number); sort also by difficulty, type, confidence."""
        ...

    def facets(self, org_id: uuid.UUID, req: SearchRequest, f: ResolvedFilters) -> dict[str, dict[str, int]]:
        """Counts per subject / type / difficulty / grade / period / school year / tag / topic (subtree); each facet
        applies every filter but its own."""
        ...

    def ids(self, org_id: uuid.UUID, f: ResolvedFilters) -> list[uuid.UUID]: ...

    def classification(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, tuple[str | None, list[uuid.UUID]]]:
        """{question id: (ltree path of its primary topic, its tag ids)}."""
        ...

    def demo(self, org_id: uuid.UUID) -> Question | None: ...


class ItemStatsReader(Protocol):
    """The graded answers of one question, aggregated (never row by row): the same read model the search columns and
    the key audit are built on."""

    def stats(self, org_id: uuid.UUID, q: Question) -> ItemStats:
        """Measured as they are — `enough_data` stays false here; the handler decides what may be shown."""
        ...


class ReviewReader(Protocol):
    def search_documents(self, org_id: uuid.UUID, req: SearchRequest, assigned_to: uuid.UUID | None = None) -> Page[ReviewDocumentView]:
        """Parsed documents with their review counts. Filters: filename, source_name (text) · assigned_to (uuid) ·
        created_at (date); sort also by total, needs_review."""
        ...

    def document(self, org_id: uuid.UUID, document_id: uuid.UUID) -> ReviewDocumentView | None: ...

    def flagged(self, org_id: uuid.UUID, req: SearchRequest) -> Page[Question]:
        """Questions whose key the audit suspects. Filters: stem (text) · updated_at (date)."""
        ...
