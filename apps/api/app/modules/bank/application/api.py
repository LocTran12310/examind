"""What other contexts, the worker and the bootstrap may ask the bank (architecture-refactor ADR-01)."""
import uuid

from app.modules.bank.application.commands.audit_keys import AuditKeys, AuditKeysHandler
from app.modules.bank.application.commands.triage_legacy_drafts import TriageLegacyDraftsHandler
from app.modules.bank.application.commands.triage_questions import TriageQuestions, TriageQuestionsHandler
from app.modules.bank.application.common import resolve_filters
from app.modules.bank.application.dto import BankFilters, QuestionView, TriageCounts
from app.modules.bank.application.ports import QuestionReader
from app.modules.bank.domain.entities import Question
from app.modules.bank.domain.ports import AnswerStats, DocumentQuestions, DuplicateFinder, QuestionRepository, ReviewLog, Taxonomy
from app.shared.application.unit_of_work import UnitOfWork


class BankApi:
    def __init__(self, questions: QuestionRepository, reader: QuestionReader, taxonomy: Taxonomy, duplicates: DuplicateFinder,
                 stats: AnswerStats, log: ReviewLog, uow: UnitOfWork, documents: DocumentQuestions | None = None):
        self.questions, self.reader, self.taxonomy, self.duplicates, self.stats, self.log, self.uow = (
            questions, reader, taxonomy, duplicates, stats, log, uow)
        self.documents = documents

    def question_ids(self, org_id: uuid.UUID, filters: BankFilters) -> list[uuid.UUID]:
        """Ids of the questions the bank filters select (exam blueprints draw from them), by id."""
        return self.reader.ids(org_id, resolve_filters(self.taxonomy, org_id, filters))

    def views(self, questions: list[Question], groups: dict[uuid.UUID, str] | None = None) -> list[QuestionView]:
        return self.reader.views(questions, groups)

    # ------------------------------------------------------------------ assessment (exams draw, show and grade questions)

    def questions_of(self, org_id: uuid.UUID | None, ids: list[uuid.UUID]) -> list[Question]:
        """Questions among `ids` (of the org when given), in no particular order."""
        return self.questions.many(org_id, list(ids)) if ids else []

    def of_document(self, document_id: uuid.UUID) -> list[Question]:
        """Every question parsed from a document, whatever its status."""
        return self.questions.of_document(document_id)

    def pool(self, org_id: uuid.UUID, *, subject_id: uuid.UUID | None = None, type: str | None = None, difficulty: str | None = None,
             topic_id: uuid.UUID | None = None, tag_id: uuid.UUID | None = None) -> list[uuid.UUID]:
        """Usable questions an exam blueprint row (or a swap) draws from, by id; unknown topic / tag: a validation error."""
        return self.question_ids(org_id, BankFilters(subject_id=subject_id, type=type, difficulty=difficulty, status="usable",
                                                     topic_ids=(topic_id,) if topic_id else (), tag_ids=(tag_id,) if tag_id else ()))

    def classification(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, tuple[str | None, list[uuid.UUID]]]:
        """{question id: (ltree path of its primary topic, its tag ids)} — what an answer fact records."""
        return self.reader.classification(list(ids))

    def triage(self, questions: list[Question], threshold: float, seed: str = "") -> TriageCounts:
        """Flushed with the caller's transaction (ingestion)."""
        return TriageQuestionsHandler(self.duplicates, self.uow)(TriageQuestions(questions, threshold, seed))

    def triage_legacy_drafts(self) -> int:
        """Questions stored before the review workflow existed are still `draft`: triaged once (the bootstrap commits)."""
        return TriageLegacyDraftsHandler(self.questions, self.duplicates, self.uow)()

    def audit_keys(self, org_id: uuid.UUID | None = None) -> list[uuid.UUID]:
        """Flushed with the caller's transaction (the worker commits)."""
        return AuditKeysHandler(self.questions, self.stats, self.log, self.uow)(AuditKeys(org_id))

    # ------------------------------------------------------------------ ingestion (flushed with the caller's transaction)

    def remove_document_questions(self, document_id: uuid.UUID, keep_statuses: tuple[str, ...], keep_used: bool) -> None:
        """A re-parse (keep_used: questions an exam uses stay) or the document's deletion; duplicates of the removed
        questions go back to review."""
        self.documents.remove(document_id, tuple(keep_statuses), keep_used)

    def kept_positions(self, document_id: uuid.UUID) -> set[tuple[str | None, int | None]]:
        return self.documents.positions(document_id)

    def add_parsed(self, org_id: uuid.UUID, document_id: uuid.UUID, drafts: list[dict], tag_id: uuid.UUID | None) -> list[uuid.UUID]:
        """Draft questions from a parsed document (`drafts`: the question columns), tagged with its source; ids in order."""
        qs = [Question(organization_id=org_id, source_document_id=document_id, **d) for d in drafts]
        self.documents.add_all(qs, tag_id)
        return [q.id for q in qs]

    def triage_ids(self, question_ids: list[uuid.UUID], threshold: float, seed: str = "") -> dict:
        """Triage of freshly parsed questions, in the given order (the spot-check draw depends on it)."""
        by_id = {q.id: q for q in self.questions.many(None, list(question_ids))}
        return vars(self.triage([by_id[i] for i in question_ids if i in by_id], threshold, seed))

    def nearest_topic(self, question_id: uuid.UUID) -> tuple[uuid.UUID, float] | None:
        """kNN (A-08): the primary topic of the most similar teacher-approved question and the similarity."""
        q = self.questions.many(None, [question_id])
        return self.documents.nearest_topic(q[0]) if q else None

    def suggest_topic(self, question_id: uuid.UUID, topic_id: uuid.UUID, source: str, score: float) -> None:
        """The primary topic ingestion suggests (source auto | knn | ai)."""
        self.documents.add_topic(question_id, topic_id, True, source, score)

    def follow_document(self, document_id: uuid.UUID, changes: dict, old_tag_id: uuid.UUID | None, new_tag_id: uuid.UUID | None) -> None:
        """The document's meta changed: subject / grade / đợt / loại đề of its questions follow; the source tag is swapped."""
        qs = self.questions.of_document(document_id)
        for q in qs:
            for k, v in changes.items():
                setattr(q, k, uuid.UUID(v) if k == "subject_id" and v else v)
        self.documents.swap_tag([q.id for q in qs], old_tag_id, new_tag_id)
        self.uow.flush()

    def document_questions(self, document_id: uuid.UUID) -> list[QuestionView]:
        """The questions parsed from a document with topics and tags, PHẦN then Câu order."""
        return self.reader.views(self.documents.in_order(document_id))

    def flush(self) -> None:
        self.uow.flush()
