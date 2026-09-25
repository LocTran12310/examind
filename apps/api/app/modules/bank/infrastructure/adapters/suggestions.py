"""Topic candidates and difficulty levels over the ingestion context's application API (topic-coverage ADR-03,
difficulty-at-upload ADR-02). The API object is handed in by the composition root: the bank never imports another
module, and each classifier keeps its one home."""
from typing import Protocol
import uuid

NeedsLevel = tuple[uuid.UUID, str | None, int | None, str, str, list]


class _Suggestions(Protocol):
    by_question: dict
    model_used: bool


class _Levels(Protocol):
    by_question: dict
    model_used: bool


class _IngestionApi(Protocol):
    def suggest_for(self, org_id: uuid.UUID, subject_id: uuid.UUID | None, items: list[tuple[uuid.UUID, str]],
                    use_model: bool = True) -> _Suggestions: ...

    def levels_for(self, org_id: uuid.UUID, items: list[NeedsLevel], use_model: bool = True) -> _Levels: ...


class IngestionTopicSuggestions:
    def __init__(self, ingestion: _IngestionApi):
        self.ingestion = ingestion

    def suggest_for(self, org_id: uuid.UUID, subject_id: uuid.UUID | None, items: list[tuple[uuid.UUID, str]],
                    use_model: bool = True) -> tuple[dict[uuid.UUID, list[tuple[uuid.UUID, float, str]]], bool]:
        found = self.ingestion.suggest_for(org_id, subject_id, list(items), use_model)
        return ({qid: [(c.topic_id, c.score, c.source) for c in candidates]
                 for qid, candidates in found.by_question.items()}, found.model_used)


class IngestionDifficultyLevels:
    """The difficulty half, registered separately from the topic half: same context behind it, but a backfill that
    needs levels must not have to know anything about topics to ask for them."""

    def __init__(self, ingestion: _IngestionApi):
        self.ingestion = ingestion

    def levels_for(self, org_id: uuid.UUID, items: list[NeedsLevel],
                   use_model: bool = True) -> tuple[dict[uuid.UUID, tuple[str, str]], bool]:
        found = self.ingestion.levels_for(org_id, list(items), use_model)
        return dict(found.by_question), found.model_used
