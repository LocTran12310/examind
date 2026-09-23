from dataclasses import dataclass
import uuid

from app.modules.bank.application.dto import TopicSuggestionView
from app.modules.bank.domain.entities import Question
from app.modules.bank.domain.ports import QuestionRepository, Taxonomy, TopicSuggestions
from app.shared.application.actor import Actor
from app.shared.domain.errors import Invalid, NotFound

MAX_QUESTIONS = 50


@dataclass(frozen=True)
class SuggestTopics:
    question_ids: list[uuid.UUID]


def _text(q: Question) -> str:
    """What the classifier reads: the stem and the options' content."""
    return q.stem + "\n" + " ".join(o.get("content", "") for o in q.options or [])


class SuggestTopicsHandler:
    """Topic candidates for the tagging queue (topic-coverage ADR-01, ADR-03). The rules live in ingestion; the bank
    asks for them a batch at a time, per subject, and stores nothing — only a teacher's choice is written."""

    def __init__(self, questions: QuestionRepository, taxonomy: Taxonomy, suggestions: TopicSuggestions):
        self.questions, self.taxonomy, self.suggestions = questions, taxonomy, suggestions

    def __call__(self, actor: Actor, query: SuggestTopics) -> dict[uuid.UUID, list[TopicSuggestionView]]:
        ids = list(dict.fromkeys(query.question_ids))
        if len(ids) > MAX_QUESTIONS:
            raise Invalid(f"Tối đa {MAX_QUESTIONS} câu hỏi mỗi lần", "question_ids")
        found = {q.id: q for q in self.questions.many(actor.org_id, ids)}
        missing = [i for i in ids if i not in found]
        if missing:
            raise NotFound("Không tìm thấy câu hỏi")
        by_subject: dict[uuid.UUID | None, list[tuple[uuid.UUID, str]]] = {}
        for i in ids:
            by_subject.setdefault(found[i].subject_id, []).append((i, _text(found[i])))
        raw: dict[uuid.UUID, list[tuple[uuid.UUID, float, str]]] = {}
        for subject_id, items in by_subject.items():
            raw.update(self.suggestions.suggest_for(actor.org_id, subject_id, items))
        labels = self.taxonomy.topic_labels(actor.org_id, [t for cs in raw.values() for t, _, _ in cs])
        return {i: [TopicSuggestionView(topic_id=t, name=labels[t][0], path=labels[t][1], score=score, source=source)
                    for t, score, source in raw.get(i, []) if t in labels]
                for i in ids}
