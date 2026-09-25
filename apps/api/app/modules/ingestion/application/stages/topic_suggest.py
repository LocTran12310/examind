"""Suggest a primary topic for each parsed question (US-06, A-13).

Keyword rules always run: every node of the org's tree contributes its own name plus curated
synonyms; the deepest, best-scoring node wins. A weak or missing keyword match falls back to kNN
over approved questions, and only what is still weak goes to the tagging model (source `ai`).
A 7B model mis-picks where the text has cues (golden run 2026-09-22), so it never overrides a strong
keyword, and over a weak one it may only refine to a descendant of that topic.
What nothing could place waits for a teacher instead of being auto-approved (topic-coverage ADR-02, A-02).
"""
from dataclasses import dataclass
import uuid

from app.modules.ingestion.application.models import usable_model
from app.modules.ingestion.application.run import IngestRun
from app.modules.ingestion.application.tagging import TopicModelPass
from app.modules.ingestion.domain.errors import LlmError
from app.modules.ingestion.domain.ports import AiModelRepository, ChatModels, QuestionBank, Taxonomy, TopicNode
from app.modules.ingestion.domain.services.splitter import ParsedQuestion
from app.modules.ingestion.domain.services.topic_rules import (
    KNN_MIN_SIMILARITY,
    WEAK_KEYWORD,
    _may_replace,
    cue_text,
    keyword_candidates,
)


@dataclass(frozen=True)
class Stored:
    """A parsed question as the bank stored it."""
    id: uuid.UUID
    stem: str
    options: list


class TopicSuggester:
    def __init__(self, taxonomy: Taxonomy, bank: QuestionBank, models: AiModelRepository, chat: ChatModels):
        self.taxonomy, self.bank, self.models, self.chat = taxonomy, bank, models, chat

    def _candidates(self, doc) -> list[TopicNode]:
        subject_id = (doc.meta or {}).get("subject_id")
        if not subject_id:
            subject_id = self.taxonomy.subject_id_by_code(doc.organization_id, "toan")
        return self.taxonomy.topics(doc.organization_id, subject_id)

    def _ai_choose(self, doc, rows: list[tuple[ParsedQuestion, Stored]], topics: list[TopicNode], run: IngestRun) -> dict:
        tag_model = (doc.processing_config or {}).get("tag_model")
        m = usable_model(self.models, doc.organization_id, tag_model) if tag_model else None
        if m is None or not topics:
            return {}
        model = TopicModelPass(self.chat, m, topics)
        out: dict = {}
        for batch in model.batches([(q.id, q.stem) for p, q in rows]):
            try:
                found = model.ask(batch)
            except LlmError as exc:
                run.warnings.append(f"Model gắn chuyên đề lỗi: {exc}")
                return out
            out.update({qid: (topic, conf, m.model) for qid, (topic, conf) in found.items()})
        return out

    def _knn(self, q: Stored) -> tuple[TopicNode | None, float] | None:
        """A-08: the primary topic of the most similar teacher-approved question (any subject of the org)."""
        near = self.bank.nearest_topic(q.id)
        if near is None or near[1] < KNN_MIN_SIMILARITY:
            return None
        return self.taxonomy.topic(near[0]), round(float(near[1]), 2)

    def _local_topic(self, q: Stored, topics: list[TopicNode]) -> tuple[TopicNode | None, float, str]:
        best = keyword_candidates(cue_text(q.stem, q.options), topics)
        topic, score, source = None, 0.0, "auto"
        if best:
            topic, score = best[0]
        if score < WEAK_KEYWORD:
            near = self._knn(q)
            if near and near[1] >= score:
                topic, score, source = near[0], near[1], "knn"
        return topic, score, source

    def __call__(self, doc, rows: list[tuple[ParsedQuestion, Stored]], run: IngestRun) -> None:
        topics = self._candidates(doc)
        if not topics or not rows:
            return
        local = {q.id: self._local_topic(q, topics) for _, q in rows}
        weak = [(p, q) for p, q in rows if local[q.id][1] < WEAK_KEYWORD]
        ai = self._ai_choose(doc, weak, topics, run) if weak else {}
        counts = {"auto": 0, "knn": 0, "ai": 0}
        untagged: list[uuid.UUID] = []
        for _, q in rows:
            topic, score, source = local[q.id]
            if q.id in ai and _may_replace(topic, ai[q.id][0]):
                topic, score, _ = ai[q.id]
                source = "ai"
            if topic is None:
                untagged.append(q.id)
                continue
            counts[source] += 1
            self.bank.suggest_topic(q.id, topic.id, source, round(score, 2))
        self.bank.flush()
        run.step("suggest_topics", keyword=counts["auto"], ai=counts["ai"], knn=counts["knn"], none=len(untagged))
        if untagged:
            # ADR-02: an unplaced question waits for a teacher instead of slipping through as auto-approved (A-02)
            self.bank.review_untagged(untagged)
            run.warnings.append(f"{len(untagged)} câu chưa gắn chuyên đề, đã chuyển sang chờ duyệt")
