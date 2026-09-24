"""QuestionBank over the bank context's application API. The API object is handed in by the composition root:
ingestion never imports another module."""
from typing import Protocol
import uuid


class _BankApi(Protocol):
    def remove_document_questions(self, document_id: uuid.UUID, keep_statuses: tuple[str, ...], keep_used: bool) -> None: ...

    def kept_positions(self, document_id: uuid.UUID) -> set[tuple[str | None, int | None]]: ...

    def add_parsed(self, org_id: uuid.UUID, document_id: uuid.UUID, drafts: list[dict], tag_id: uuid.UUID | None) -> list[uuid.UUID]: ...

    def triage_ids(self, question_ids: list[uuid.UUID], threshold: float, seed: str = "") -> dict: ...

    def nearest_topic(self, question_id: uuid.UUID) -> tuple[uuid.UUID, float] | None: ...

    def nearest_topics(self, org_id: uuid.UUID, subject_id: uuid.UUID | None, question_id: uuid.UUID,
                       limit: int) -> list[tuple[uuid.UUID, float]]: ...

    def suggest_topic(self, question_id: uuid.UUID, topic_id: uuid.UUID, source: str, score: float) -> None: ...

    def set_difficulty(self, levels: dict[uuid.UUID, tuple[str, str]]) -> dict[str, int]: ...

    def review_untagged(self, question_ids: list[uuid.UUID]) -> int: ...

    def follow_document(self, document_id: uuid.UUID, changes: dict, old_tag_id: uuid.UUID | None, new_tag_id: uuid.UUID | None) -> None: ...

    def flush(self) -> None: ...


class BankAdapter:
    def __init__(self, bank: _BankApi):
        self.bank = bank

    def remove_document_questions(self, document_id: uuid.UUID, keep_statuses: tuple[str, ...], keep_used: bool) -> None:
        self.bank.remove_document_questions(document_id, keep_statuses, keep_used)

    def kept_positions(self, document_id: uuid.UUID) -> set[tuple[str | None, int | None]]:
        return self.bank.kept_positions(document_id)

    def add_parsed(self, org_id: uuid.UUID, document_id: uuid.UUID, drafts: list[dict], tag_id: uuid.UUID | None) -> list[uuid.UUID]:
        return self.bank.add_parsed(org_id, document_id, drafts, tag_id)

    def triage(self, question_ids: list[uuid.UUID], threshold: float, seed: str) -> dict:
        return self.bank.triage_ids(question_ids, threshold, seed)

    def nearest_topic(self, question_id: uuid.UUID) -> tuple[uuid.UUID, float] | None:
        return self.bank.nearest_topic(question_id)

    def nearest_topics(self, org_id: uuid.UUID, subject_id: uuid.UUID | None, question_id: uuid.UUID,
                       limit: int) -> list[tuple[uuid.UUID, float]]:
        return self.bank.nearest_topics(org_id, subject_id, question_id, limit)

    def suggest_topic(self, question_id: uuid.UUID, topic_id: uuid.UUID, source: str, score: float) -> None:
        self.bank.suggest_topic(question_id, topic_id, source, score)

    def set_difficulty(self, levels: dict[uuid.UUID, tuple[str, str]]) -> dict[str, int]:
        return self.bank.set_difficulty(levels)

    def review_untagged(self, question_ids: list[uuid.UUID]) -> int:
        return self.bank.review_untagged(question_ids)

    def follow_document(self, document_id: uuid.UUID, changes: dict, old_tag_id: uuid.UUID | None, new_tag_id: uuid.UUID | None) -> None:
        self.bank.follow_document(document_id, changes, old_tag_id, new_tag_id)

    def flush(self) -> None:
        self.bank.flush()
