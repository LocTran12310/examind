"""What other contexts may ask the ingestion context (architecture-refactor ADR-01): the topic classifier and the
difficulty classifier, on demand."""
from dataclasses import dataclass
import uuid

from app.modules.ingestion.application.difficulty import DifficultyModelPass
from app.modules.ingestion.application.models import usable_model
from app.modules.ingestion.application.tagging import TopicModelPass
from app.modules.ingestion.domain.ports import AiModelRepository, ChatModels, OrgSettings, QuestionBank, Taxonomy, TopicNode
from app.modules.ingestion.domain.services.difficulty_rules import difficulty_for, question_text
from app.modules.ingestion.domain.services.processing import org_defaults
from app.modules.ingestion.domain.services.topic_rules import KNN_MIN_SIMILARITY, WEAK_KEYWORD, keyword_candidates

MAX_SUGGESTIONS = 3
MODEL_TIMEOUT_SECONDS = 60.0  # a page of the queue waits for the model, so it is bounded much tighter than a job (A-06)


@dataclass(frozen=True)
class TopicSuggestion:
    """A candidate topic for a question nobody placed yet; `source` says where it came from."""
    topic_id: uuid.UUID
    score: float
    source: str  # keyword | similar | ai


@dataclass(frozen=True)
class Suggestions:
    """Candidates per question, and whether the tagging model actually answered (topic-coverage AC-07)."""
    by_question: dict[uuid.UUID, list[TopicSuggestion]]
    model_used: bool


#: one question to be levelled: (id, part, number, type, stem, options) — everything both signals read
NeedsLevel = tuple[uuid.UUID, str | None, int | None, str, str, list]


@dataclass(frozen=True)
class Levels:
    """`{question id: (level, source)}` and whether the model answered at all (difficulty-at-upload AC-05)."""
    by_question: dict[uuid.UUID, tuple[str, str]]
    model_used: bool


SOURCE_ORDER = {"keyword": 0, "similar": 1, "ai": 2}


def _shortlist(candidates: list[TopicSuggestion]) -> list[TopicSuggestion]:
    """At most three, rules first; a model candidate keeps the last slot instead of being cut off, because it is
    the one that may come from a different branch than the neighbours."""
    rules = [c for c in candidates if c.source != "ai"]
    ai = [c for c in candidates if c.source == "ai"]
    if not ai:
        return rules[:MAX_SUGGESTIONS]
    return rules[:MAX_SUGGESTIONS - 1] + ai[:1]


class IngestionApi:
    def __init__(self, taxonomy: Taxonomy, bank: QuestionBank, settings: OrgSettings | None = None,
                 models: AiModelRepository | None = None, chat: ChatModels | None = None,
                 timeout: float | None = MODEL_TIMEOUT_SECONDS):
        self.taxonomy, self.bank = taxonomy, bank
        self.settings, self.models, self.chat, self.timeout = settings, models, chat, timeout

    def suggest_for(self, org_id: uuid.UUID, subject_id: uuid.UUID | None, items: list[tuple[uuid.UUID, str]],
                    use_model: bool = True) -> Suggestions:
        """Topic candidates for questions of one subject (topic-coverage ADR-01, ADR-04): the pipeline's keyword cues,
        then kNN over the already-tagged questions of the subject, and for whatever is still without a candidate — or
        with a weak one — the org's tagging model, in batches (ADR-04, A-07). The rules keep the lead: a question
        the cues placed strongly never reaches the model, and in the answer a rule candidate always comes first."""
        topics = self.taxonomy.topics(org_id, subject_id) if items else []
        found = {question_id: self._rule_candidates(org_id, subject_id, question_id, text, topics)
                 for question_id, text in items}
        weak = [(qid, text) for qid, text in items if not found[qid] or found[qid][0].score < WEAK_KEYWORD]
        model_used = self._model_pass(org_id, topics, weak, found) if use_model and weak and topics else False
        # a rule candidate always leads: cues and neighbours are deterministic and checkable, while a read of eight
        # `ai` candidates by hand found two plainly wrong (2026-09-23), so the model fills gaps instead of leading
        for candidates in found.values():
            candidates.sort(key=lambda c: (SOURCE_ORDER[c.source], -c.score))
        return Suggestions({qid: _shortlist(cs) for qid, cs in found.items()}, model_used)

    def levels_for(self, org_id: uuid.UUID, items: list[NeedsLevel], use_model: bool = True) -> Levels:
        """The level of each question, decided the way the pipeline decides it (difficulty-at-upload ADR-02): the
        position rule answers every one of them, then the org's classification model replaces what it can read.

        Same division of labour as `suggest_for`, and the opposite lead. There the rules lead because they are
        deterministic and checkable; here the rule is a *convention about where a question sits in a paper* and
        carries no information the caller does not already have — `difficulty_for` is a pure function of part,
        number and type. The model's answer is the only one that read the question, so it leads (ADR-03).
        """
        rule = {qid: (difficulty_for(part, number, qtype), "auto") for qid, part, number, qtype, _, _ in items}
        m = self._tagging_model(org_id) if use_model and items else None
        if m is None:
            return Levels(rule, False)
        model = DifficultyModelPass(self.chat, m, timeout=self.timeout)
        rows = [(qid, i + 1, question_text(stem, qtype, options))
                for i, (qid, _, _, qtype, stem, options) in enumerate(items)]
        answered = False
        for batch in model.batches(rows):
            try:
                got = model.ask(batch)
            except Exception:  # noqa: BLE001 — a failed batch leaves the rule's answer standing, like the pipeline's
                continue
            answered = True
            for qid, level in got.items():
                rule[qid] = (level, "ai")
        return Levels(rule, answered)

    def _rule_candidates(self, org_id: uuid.UUID, subject_id: uuid.UUID | None, question_id: uuid.UUID, text: str,
                         topics: list[TopicNode]) -> list[TopicSuggestion]:
        found = [TopicSuggestion(t.id, score, "keyword") for t, score in keyword_candidates(text, topics, MAX_SUGGESTIONS)]
        if not found or found[0].score < WEAK_KEYWORD:
            seen = {c.topic_id for c in found}
            for topic_id, similarity in self.bank.nearest_topics(org_id, subject_id, question_id, MAX_SUGGESTIONS):
                if similarity >= KNN_MIN_SIMILARITY and topic_id not in seen:
                    found.append(TopicSuggestion(topic_id, round(float(similarity), 2), "similar"))
        return found

    def _model_pass(self, org_id: uuid.UUID, topics: list[TopicNode], weak: list[tuple[uuid.UUID, str]],
                    found: dict[uuid.UUID, list[TopicSuggestion]]) -> bool:
        """Ask the org's tagging model about the questions the rules left weak; True when it answered at all. A model
        that is missing, disabled, failing or slow simply leaves the rule candidates alone (AC-07)."""
        m = self._tagging_model(org_id)
        if m is None:
            return False
        model = TopicModelPass(self.chat, m, topics, timeout=self.timeout)
        answered = False
        for batch in model.batches([(qid, i + 1, text) for i, (qid, text) in enumerate(weak)]):
            try:
                chosen = model.ask(batch)
            except Exception:  # noqa: BLE001 — the queue never fails because a model did; the other batches still count
                continue
            answered = True
            for qid, (topic, confidence) in chosen.items():
                if topic.id not in {c.topic_id for c in found[qid]}:
                    found[qid].append(TopicSuggestion(topic.id, round(min(0.95, max(0.0, confidence)), 2), "ai"))
        return answered

    def _tagging_model(self, org_id: uuid.UUID):
        """The org's enabled tagging model, or None when it has none — the queue is wired with the model ports, the
        worker's copy of the API is not."""
        if self.settings is None or self.models is None or self.chat is None:
            return None
        try:
            tag_model = org_defaults(self.settings.ingestion(org_id)).get("tag_model")
        except Exception:  # noqa: BLE001 — unreadable settings are a missing model, not a failed request
            return None
        return usable_model(self.models, org_id, tag_model) if tag_model else None
