"""The org's model asked what level each question is (difficulty-at-upload ADR-02).

Built like the tagging pass and for the same reason: one wording, one batch size, one way a reply becomes levels,
so the pipeline stage and anything that asks later cannot drift apart. A batch raises `LlmError`; the caller
decides what that costs — for the pipeline it costs a warning and the position rule keeps every question.
"""
from collections.abc import Iterator
from typing import Any

from app.modules.ingestion.domain.entities import AiModel
from app.modules.ingestion.domain.ports import ChatModels
from app.modules.ingestion.domain.services.difficulty_rules import (
    DIFFICULTY_BATCH,
    DIFFICULTY_SYSTEM,
    difficulty_request,
    read_difficulty_reply,
)

Row = tuple[Any, int, str]  # (caller key, the number the prompt gives the question, its text)


class DifficultyModelPass:
    """One model over the questions of one document, in batches of `DIFFICULTY_BATCH`."""

    def __init__(self, chat: ChatModels, model: AiModel, timeout: float | None = None):
        self.chat, self.model, self.timeout = chat, model, timeout

    def batches(self, rows: list[Row]) -> Iterator[list[Row]]:
        for start in range(0, len(rows), DIFFICULTY_BATCH):
            yield rows[start:start + DIFFICULTY_BATCH]

    def ask(self, batch: list[Row]) -> dict[Any, str]:
        """{caller key: level} for one batch; raises LlmError when the model fails or rambles."""
        reply = self.chat.chat(self.model, DIFFICULTY_SYSTEM, difficulty_request([(n, t) for _, n, t in batch]),
                               timeout=self.timeout)
        return read_difficulty_reply(reply.text, {n: key for key, n, _ in batch})
