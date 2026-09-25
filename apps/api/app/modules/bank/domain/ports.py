from typing import Protocol
import uuid

from app.modules.bank.domain.entities import Question, ReviewEvent


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

    def with_status(self, status: str) -> list[Question]:
        """Every question of every org in that status (maintenance passes)."""
        ...

    def without_difficulty(self, org_id: uuid.UUID, limit: int) -> list[Question]:
        """Usable questions of the org that carry no level yet, oldest first — what the backfill has left to do.

        Oldest first so that re-running the command walks the backlog instead of circling the same page, and only
        usable ones because a rejected or duplicate question is not what an empty blueprint row is short of.
        """
        ...

    def count_without_difficulty(self, org_id: uuid.UUID) -> int:
        """How many of those there are, so a bounded run can say what is left (AC-05)."""
        ...

    def add(self, q: Question) -> None: ...

    def remove(self, q: Question) -> None: ...

    def release_duplicates_of(self, question_ids: list[uuid.UUID]) -> None:
        """Copies marked "duplicate" of these go back to review (otherwise they stay hidden as duplicates of nothing)."""
        ...

    def replace_topics(self, question_id: uuid.UUID, topic_ids: list[uuid.UUID], primary_id: uuid.UUID | None) -> None:
        """Manual placement: the links become exactly `topic_ids` (source manual, score 1)."""
        ...

    def primary_topic_ids(self, question_ids: list[uuid.UUID]) -> dict[uuid.UUID, uuid.UUID]:
        """The primary topic of each of these questions that has one."""
        ...

    def topic_ids(self, question_id: uuid.UUID) -> tuple[list[uuid.UUID], uuid.UUID | None]:
        """Where the question sits now: (its topics, the primary one) — what a review event records as the before
        of a placement, and what `replace_topics` would take to put it back."""
        ...

    def tag_ids(self, question_id: uuid.UUID) -> set[uuid.UUID]: ...

    def replace_tags(self, question_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> None: ...


class ReviewLog(Protocol):
    """Append-only review history."""

    def record(self, org_id: uuid.UUID, user_id: uuid.UUID | None, question_id: uuid.UUID | None, action: str,
               before: dict | None, after: dict | None, batch_id: uuid.UUID | None = None) -> None:
        """`batch_id` groups the events of one request; a command passes the same id to every event it writes."""
        ...

    def batch(self, org_id: uuid.UUID, batch_id: uuid.UUID) -> list[ReviewEvent]:
        """Every event that request wrote in this organisation, oldest first — what an undo reads to rebuild the
        state its questions were in. Empty when the organisation has no such batch."""
        ...

    def undone_by(self, org_id: uuid.UUID, batch_id: uuid.UUID) -> uuid.UUID | None:
        """The batch of the `undo` that already took this one back (A-04), or None while none has."""
        ...

    def recent_spot_actions(self, org_id: uuid.UUID, limit: int) -> list[str]:
        """spot_ok / spot_fail actions, newest first."""
        ...


class Taxonomy(Protocol):
    """The taxonomy context, seen from the bank (its application API behind an adapter)."""

    def topic_paths(self, org_id: uuid.UUID, topic_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        """ltree path of each topic of the org among `topic_ids` (unknown ones are missing)."""
        ...

    def topic_labels(self, org_id: uuid.UUID, topic_ids: list[uuid.UUID]) -> dict[uuid.UUID, tuple[str, str]]:
        """(name, ltree path) of each topic of the org among `topic_ids` (unknown ones are missing)."""
        ...

    def topic_subjects(self, org_id: uuid.UUID, topic_ids: list[uuid.UUID]) -> dict[uuid.UUID, uuid.UUID]:
        """subject of each topic of the org among `topic_ids` (unknown ones are missing)."""
        ...

    def tag_groups(self, org_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        """group of each tag of the org among `tag_ids` (unknown ones are missing)."""
        ...

    def subject_exists(self, org_id: uuid.UUID, subject_id: uuid.UUID) -> bool: ...

    def grade_levels(self, org_id: uuid.UUID) -> set[int]:
        """The levels of the grades the org keeps."""
        ...


class TopicSuggestions(Protocol):
    """The ingestion context's classifier, seen from the bank (topic-coverage ADR-03): candidates for questions
    nobody has placed yet, computed on demand and never stored."""

    def suggest_for(self, org_id: uuid.UUID, subject_id: uuid.UUID | None, items: list[tuple[uuid.UUID, str]],
                    use_model: bool = True) -> tuple[dict[uuid.UUID, list[tuple[uuid.UUID, float, str]]], bool]:
        """({question id: [(topic id, score, source)]}, whether the tagging model answered) — at most three
        candidates, best first; source `keyword` | `similar` | `ai` (topic-coverage ADR-04)."""
        ...


#: one question to be levelled, as the bank hands it over: (id, part, number, type, stem, options)
NeedsLevel = tuple[uuid.UUID, str | None, int | None, str, str, list]


class DifficultyLevels(Protocol):
    """The ingestion context's difficulty classifier, seen from the bank (difficulty-at-upload ADR-02): the level a
    question's place in the paper implies, with the org's model over it where the model can read the question."""

    def levels_for(self, org_id: uuid.UUID, items: list[NeedsLevel],
                   use_model: bool = True) -> tuple[dict[uuid.UUID, tuple[str, str]], bool]:
        """({question id: (level, source)}, whether the model answered). `source` is `auto` for the position rule
        and `ai` for the model; every question asked about comes back with a level."""
        ...


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


class DocumentQuestions(Protocol):
    """The questions parsed from one source document, handled as a set (ingestion: re-parse, delete, meta edits)."""

    def in_order(self, document_id: uuid.UUID) -> list[Question]:
        """PHẦN then Câu order (questions without a part first)."""
        ...

    def remove(self, document_id: uuid.UUID, keep_statuses: tuple[str, ...], keep_used: bool) -> None:
        """Delete all but the kept statuses (and, with keep_used, those an exam uses); their duplicates go back to review."""
        ...

    def positions(self, document_id: uuid.UUID) -> set[tuple[str | None, int | None]]: ...

    def add_all(self, questions: list[Question], tag_id: uuid.UUID | None) -> None: ...

    def nearest_topic(self, q: Question) -> tuple[uuid.UUID, float] | None:
        """(primary topic, similarity) of the most similar approved question of the org (pg_trgm)."""
        ...

    def nearest_topics(self, org_id: uuid.UUID, subject_id: uuid.UUID | None, question_id: uuid.UUID,
                       limit: int) -> list[tuple[uuid.UUID, float]]:
        """The primary topics of the usable questions of that subject whose text looks most like this one's:
        (topic, similarity), best first (topic-coverage ADR-01)."""
        ...

    def add_topic(self, question_id: uuid.UUID, topic_id: uuid.UUID, is_primary: bool, source: str, score: float | None) -> None: ...

    def swap_tag(self, question_ids: list[uuid.UUID], old_tag_id: uuid.UUID | None, new_tag_id: uuid.UUID | None) -> None: ...
