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

Row = tuple[Any, int, str]  # (caller key, the number the prompt gives the question, its text)


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
        reply = self.chat.chat(self.model, TAG_SYSTEM, tag_request(self.listing, [(n, t) for _, n, t in batch]),
                               timeout=self.timeout)
        return read_tag_reply(reply.text, self.topics, {n: key for key, n, _ in batch})
