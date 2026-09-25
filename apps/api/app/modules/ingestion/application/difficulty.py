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

#: (caller key, the question's text). The number the prompt uses is **not** the caller's to choose: `ask` assigns
#: it by position in the batch. A caller that passed the paper's own number produced a prompt asking about "câu 1"
#: twice — THPT numbering restarts at each phần — and the reply's numbers then mapped to one question instead of
#: two, so 72 of 18 papers' Phần II questions silently lost their level (difficulty-at-upload T-02-04).
Row = tuple[Any, str]


class DifficultyModelPass:
    """One model over the questions of one document, in batches of `DIFFICULTY_BATCH`."""

    def __init__(self, chat: ChatModels, model: AiModel, timeout: float | None = None):
        self.chat, self.model, self.timeout = chat, model, timeout

    def batches(self, rows: list[Row]) -> Iterator[list[Row]]:
        for start in range(0, len(rows), DIFFICULTY_BATCH):
            yield rows[start:start + DIFFICULTY_BATCH]

    def ask(self, batch: list[Row]) -> dict[Any, str]:
        """{caller key: level} for one batch; raises LlmError when the model fails or rambles.

        The questions are numbered 1..n here, by their place in this batch, so the numbers are unique by
        construction and mean nothing beyond "which answer belongs to which question".
        """
        numbered = [(i + 1, text) for i, (_, text) in enumerate(batch)]
        reply = self.chat.chat(self.model, DIFFICULTY_SYSTEM, difficulty_request(numbered), timeout=self.timeout)
        return read_difficulty_reply(reply.text, {i + 1: key for i, (key, _) in enumerate(batch)})
