"""What other contexts may ask the ingestion context (architecture-refactor ADR-01): the topic classifier, on demand."""
from dataclasses import dataclass
import uuid

from app.modules.ingestion.domain.ports import QuestionBank, Taxonomy
from app.modules.ingestion.domain.services.topic_rules import KNN_MIN_SIMILARITY, WEAK_KEYWORD, keyword_candidates

MAX_SUGGESTIONS = 3


@dataclass(frozen=True)
class TopicSuggestion:
    """A candidate topic for a question nobody placed yet; `source` says where it came from."""
    topic_id: uuid.UUID
    score: float
    source: str  # keyword | similar


class IngestionApi:
    def __init__(self, taxonomy: Taxonomy, bank: QuestionBank):
        self.taxonomy, self.bank = taxonomy, bank

    def suggest_for(self, org_id: uuid.UUID, subject_id: uuid.UUID | None,
                    items: list[tuple[uuid.UUID, str]]) -> dict[uuid.UUID, list[TopicSuggestion]]:
        """Topic candidates for questions of one subject (topic-coverage ADR-01): the pipeline's keyword cues, then
        kNN over the already-tagged questions of the subject for whatever the cues leave weak. The tagging model is
        never called (A-05) — a teacher is choosing between three candidates, not waiting for a model."""
        topics = self.taxonomy.topics(org_id, subject_id) if items else []
        out: dict[uuid.UUID, list[TopicSuggestion]] = {}
        for question_id, text in items:
            found = [TopicSuggestion(t.id, score, "keyword") for t, score in keyword_candidates(text, topics, MAX_SUGGESTIONS)]
            if not found or found[0].score < WEAK_KEYWORD:
                seen = {c.topic_id for c in found}
                for topic_id, similarity in self.bank.nearest_topics(org_id, subject_id, question_id, MAX_SUGGESTIONS):
                    if similarity >= KNN_MIN_SIMILARITY and topic_id not in seen:
                        found.append(TopicSuggestion(topic_id, round(float(similarity), 2), "similar"))
            found.sort(key=lambda c: -c.score)  # stable: a keyword cue wins a tie with a neighbour
            out[question_id] = found[:MAX_SUGGESTIONS]
        return out
