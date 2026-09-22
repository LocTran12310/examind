from typing import Protocol
import uuid

from app.modules.bank.domain.entities import Question


class QuestionRepository(Protocol):
    """The question aggregate: content + review state, with its topic and tag links."""

    def get(self, org_id: uuid.UUID, question_id: uuid.UUID) -> Question | None: ...

    def many(self, org_id: uuid.UUID | None, ids: list[uuid.UUID]) -> list[Question]:
        """Questions of the org among `ids` (every org when org_id is None: the background key audit)."""
        ...

    def review_queue(self, document_id: uuid.UUID) -> list[Question]:
        """What a teacher still has to look at in a document: needs review, flagged, spot checks pending."""
        ...

    def of_document(self, document_id: uuid.UUID, *, type: str | None = None, status: str | None = None,
                    spot_check: bool | None = None) -> list[Question]: ...

    def add(self, q: Question) -> None: ...

    def remove(self, q: Question) -> None: ...

    def release_duplicates_of(self, question_ids: list[uuid.UUID]) -> None:
        """Copies marked "duplicate" of these go back to review (otherwise they stay hidden as duplicates of nothing)."""
        ...

    def replace_topics(self, question_id: uuid.UUID, topic_ids: list[uuid.UUID], primary_id: uuid.UUID | None) -> None:
        """Manual placement: the links become exactly `topic_ids` (source manual, score 1)."""
        ...

    def tag_ids(self, question_id: uuid.UUID) -> set[uuid.UUID]: ...

    def replace_tags(self, question_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> None: ...


class ReviewLog(Protocol):
    """Append-only review history."""

    def record(self, org_id: uuid.UUID, user_id: uuid.UUID | None, question_id: uuid.UUID | None, action: str,
               before: dict | None, after: dict | None) -> None: ...

    def recent_spot_actions(self, org_id: uuid.UUID, limit: int) -> list[str]:
        """spot_ok / spot_fail actions, newest first."""
        ...


class Taxonomy(Protocol):
    """The taxonomy context, seen from the bank (its application API behind an adapter)."""

    def topic_paths(self, org_id: uuid.UUID, topic_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        """ltree path of each topic of the org among `topic_ids` (unknown ones are missing)."""
        ...

    def tag_groups(self, org_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        """group of each tag of the org among `tag_ids` (unknown ones are missing)."""
        ...

    def subject_exists(self, org_id: uuid.UUID, subject_id: uuid.UUID) -> bool: ...


class StaffDirectory(Protocol):
    """The identity context: who may be given a document to review."""

    def is_teacher(self, org_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """An active teacher or org admin of the org (platform admins excluded)."""
        ...


class ReviewDocuments(Protocol):
    """Source documents as the review workflow sees them."""

    def exists(self, org_id: uuid.UUID, document_id: uuid.UUID) -> bool: ...

    def assign(self, org_id: uuid.UUID, document_id: uuid.UUID, user_id: uuid.UUID | None) -> None: ...


class ReviewSettings(Protocol):
    """The org's auto-approval threshold (ingestion settings)."""

    def threshold(self, org_id: uuid.UUID) -> float: ...

    def set_threshold(self, org_id: uuid.UUID, value: float) -> None: ...


class QuestionUsage(Protocol):
    """Whether another context still uses a question (e.g. an exam): it may not be deleted then."""

    def in_use(self, question_id: uuid.UUID) -> bool: ...


class AnswerStats(Protocol):
    """Submitted answers to usable MCQs, for the key audit."""

    def mcq_answers(self, org_id: uuid.UUID | None) -> dict[uuid.UUID, list[tuple[dict | None, float]]]:
        """{question_id: [(response, the attempt's score ratio)]}."""
        ...


class DuplicateFinder(Protocol):
    def similar(self, q: Question, limit: int = 5) -> list[tuple[uuid.UUID, float, str]]:
        """Usable questions of the org of the same type from another document whose search text looks alike:
        (id, similarity, search_text), most similar first."""
        ...
