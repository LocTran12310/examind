"""The tagging model's pass over the questions the rules left weak (topic-coverage ADR-04).

The pipeline stage and the bank's tagging queue both run it, so the prompt, the batch size and the way a reply is
turned back into topics live here once. A batch raises `LlmError`; what a caller does with that differs — the stage
stops and warns the teacher, the queue drops the batch and keeps whatever else came back (A-06).
"""
from collections.abc import Iterator
from typing import Any

from app.modules.ingestion.domain.entities import AiModel
from app.modules.ingestion.domain.ports import ChatModels, TopicNode
from app.modules.ingestion.domain.services.topic_rules import TAG_BATCH, TAG_SYSTEM, read_tag_reply, tag_listing, tag_request

#: (caller key, the question's text). The number the prompt uses is **not** the caller's to choose: `ask` assigns
#: it by position in the batch. A caller that passed the paper's own number produced a prompt asking about "câu 1"
#: twice — THPT numbering restarts at each phần — and the reply's numbers then mapped to one question instead of
#: two, so 72 of 18 papers' Phần II questions silently lost their level (difficulty-at-upload T-02-04).
Row = tuple[Any, str]


class TopicModelPass:
    """One model over one topic tree: the listing is built once, the questions go in batches of `TAG_BATCH`."""

    def __init__(self, chat: ChatModels, model: AiModel, topics: list[TopicNode], timeout: float | None = None):
        self.chat, self.model, self.topics, self.timeout = chat, model, topics, timeout
        self.listing = tag_listing(topics)

    def batches(self, rows: list[Row]) -> Iterator[list[Row]]:
        for start in range(0, len(rows), TAG_BATCH):
            yield rows[start:start + TAG_BATCH]

    def ask(self, batch: list[Row]) -> dict[Any, tuple[TopicNode, float]]:
        """{caller key: (topic, confidence)} for one batch; raises LlmError when the model fails or rambles."""
        numbered = [(i + 1, text) for i, (_, text) in enumerate(batch)]
        reply = self.chat.chat(self.model, TAG_SYSTEM, tag_request(self.listing, numbered), timeout=self.timeout)
        return read_tag_reply(reply.text, self.topics, {i + 1: key for i, (key, _) in enumerate(batch)})
