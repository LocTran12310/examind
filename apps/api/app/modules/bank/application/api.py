"""What other contexts (and the old layout) may ask the bank (architecture-refactor ADR-01)."""
import uuid

from app.modules.bank.application.commands.audit_keys import AuditKeys, AuditKeysHandler
from app.modules.bank.application.commands.triage_questions import TriageQuestions, TriageQuestionsHandler
from app.modules.bank.application.common import resolve_filters
from app.modules.bank.application.dto import BankFilters, QuestionView, TriageCounts
from app.modules.bank.application.ports import QuestionReader
from app.modules.bank.domain.entities import Question
from app.modules.bank.domain.ports import AnswerStats, DuplicateFinder, QuestionRepository, ReviewLog, Taxonomy
from app.shared.application.unit_of_work import UnitOfWork


class BankApi:
    def __init__(self, questions: QuestionRepository, reader: QuestionReader, taxonomy: Taxonomy, duplicates: DuplicateFinder,
                 stats: AnswerStats, log: ReviewLog, uow: UnitOfWork):
        self.questions, self.reader, self.taxonomy, self.duplicates, self.stats, self.log, self.uow = (
            questions, reader, taxonomy, duplicates, stats, log, uow)

    def question_ids(self, org_id: uuid.UUID, filters: BankFilters) -> list[uuid.UUID]:
        """Ids of the questions the bank filters select (exam blueprints draw from them), by id."""
        return self.reader.ids(org_id, resolve_filters(self.taxonomy, org_id, filters))

    def views(self, questions: list[Question], groups: dict[uuid.UUID, str] | None = None) -> list[QuestionView]:
        return self.reader.views(questions, groups)

    def triage(self, questions: list[Question], threshold: float, seed: str = "") -> TriageCounts:
        """Flushed with the caller's transaction (ingestion)."""
        return TriageQuestionsHandler(self.duplicates, self.uow)(TriageQuestions(questions, threshold, seed))

    def audit_keys(self, org_id: uuid.UUID | None = None) -> list[uuid.UUID]:
        """Flushed with the caller's transaction (the worker commits)."""
        return AuditKeysHandler(self.questions, self.stats, self.log, self.uow)(AuditKeys(org_id))
