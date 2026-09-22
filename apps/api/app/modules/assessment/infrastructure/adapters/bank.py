"""QuestionBank over the bank context's application API. The API object is handed in by the composition root:
assessment never imports another module."""
import dataclasses
from typing import Any, Protocol
import uuid

from app.modules.assessment.domain.value_objects import PoolFilter, QuestionRef


class _BankApi(Protocol):
    def questions_of(self, org_id: uuid.UUID | None, ids: list[uuid.UUID]) -> list: ...

    def of_document(self, document_id: uuid.UUID) -> list: ...

    def pool(self, org_id: uuid.UUID, *, subject_id: uuid.UUID | None = None, type: str | None = None, difficulty: str | None = None,
             topic_id: uuid.UUID | None = None, tag_id: uuid.UUID | None = None) -> list[uuid.UUID]: ...

    def views(self, questions: list, groups: dict | None = None) -> list: ...

    def classification(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, tuple[str | None, list[uuid.UUID]]]: ...


def _ref(q: Any) -> QuestionRef:
    return QuestionRef(id=q.id, organization_id=q.organization_id, type=q.type, status=q.status, stem=q.stem or "", options=list(q.options or []),
                       answer=q.answer, solution=q.solution or "", difficulty=q.difficulty, grade=q.grade, part=q.part, number=q.number,
                       source_document_id=q.source_document_id)


class BankQuestions:
    def __init__(self, bank: _BankApi):
        self.bank = bank

    def questions(self, org_id: uuid.UUID | None, ids: list[uuid.UUID]) -> list[QuestionRef]:
        return [_ref(q) for q in self.bank.questions_of(org_id, list(ids))] if ids else []

    def of_document(self, document_id: uuid.UUID) -> list[QuestionRef]:
        return [_ref(q) for q in self.bank.of_document(document_id)]

    def pool(self, org_id: uuid.UUID, f: PoolFilter) -> list[uuid.UUID]:
        return self.bank.pool(org_id, subject_id=f.subject_id, type=f.type, difficulty=f.difficulty, topic_id=f.topic_id, tag_id=f.tag_id)

    def views(self, org_id: uuid.UUID | None, ids: list[uuid.UUID]) -> dict[uuid.UUID, dict]:
        if not ids:
            return {}
        return {v.id: dataclasses.asdict(v) for v in self.bank.views(self.bank.questions_of(org_id, list(ids)))}

    def classification(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, tuple[str | None, list[uuid.UUID]]]:
        return self.bank.classification(list(ids)) if ids else {}
