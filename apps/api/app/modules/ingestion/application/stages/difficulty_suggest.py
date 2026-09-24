"""Give every parsed question a level (difficulty-at-upload ADR-02, US-01).

The position rule answers for all of them first, because a question with no level is what this feature exists to
fix: 376 of 378 questions in the bank had none, and every blueprint row that asked for a mức độ came back empty.
The org's model then reads the questions it can and its answers replace the rule's guess, since it is the only
signal that has actually seen the question (A-05).

A model that is missing, disabled, slow or talking nonsense is a **warning in the document's log**, never a
failure: the paper is still parsed and every question still has a level, exactly the way the topic pass degrades.
A level a teacher set is not touched at all (ADR-04) — that guard sits in the bank, where every writer meets it.
"""
import uuid

from app.modules.ingestion.application.difficulty import DifficultyModelPass
from app.modules.ingestion.application.models import usable_model
from app.modules.ingestion.application.run import IngestRun
from app.modules.ingestion.application.stages.topic_suggest import Stored
from app.modules.ingestion.domain.errors import LlmError
from app.modules.ingestion.domain.ports import AiModelRepository, ChatModels, QuestionBank
from app.modules.ingestion.domain.services.difficulty_rules import difficulty_for, question_text
from app.modules.ingestion.domain.services.splitter import ParsedQuestion


class DifficultySuggester:
    def __init__(self, bank: QuestionBank, models: AiModelRepository, chat: ChatModels):
        self.bank, self.models, self.chat = bank, models, chat

    def _ai_levels(self, doc, rows: list[tuple[ParsedQuestion, Stored]], run: IngestRun) -> dict[uuid.UUID, str]:
        """What the model could say. The org's classification model does this pass too: an org that registered one
        for topics gets levels from the same model, with no second setting to keep in step."""
        model_id = (doc.processing_config or {}).get("tag_model")
        m = usable_model(self.models, doc.organization_id, model_id) if model_id else None
        if m is None:
            return {}
        model = DifficultyModelPass(self.chat, m)
        out: dict[uuid.UUID, str] = {}
        for batch in model.batches([(q.id, p.number, question_text(q.stem, p.type, q.options)) for p, q in rows]):
            try:
                out.update(model.ask(batch))
            except LlmError as exc:
                run.warnings.append(f"Model đoán mức độ lỗi: {exc}")
                return out  # what came back before the failure is kept; the rule covers the rest
        return out

    def __call__(self, doc, rows: list[tuple[ParsedQuestion, Stored]], run: IngestRun) -> None:
        if not rows:
            return
        ai = self._ai_levels(doc, rows, run)
        levels = {q.id: ((ai[q.id], "ai") if q.id in ai else (difficulty_for(p.part, p.number, p.type), "auto"))
                  for p, q in rows}
        counts = self.bank.set_difficulty(levels)  # flushed with the run's transaction, like the rest of the pipeline
        run.step("suggest_difficulty", rule=counts.get("auto", 0), ai=counts.get("ai", 0))
