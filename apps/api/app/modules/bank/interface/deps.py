"""Builds the bank handlers for a request (composition of ports and adapters). The taxonomy and identity contexts
are reached through factories the composition root registers: the bank never imports another module."""
from collections.abc import Callable
import uuid

from fastapi import Depends
from sqlalchemy.orm import Session

from app.modules.bank.application.api import BankApi
from app.modules.bank.application.commands.apply_answer_key import ApplyAnswerKeyHandler
from app.modules.bank.application.commands.approve_confident import ApproveConfidentHandler
from app.modules.bank.application.commands.assign_reviewer import AssignReviewerHandler
from app.modules.bank.application.commands.audit_keys import AuditKeysHandler
from app.modules.bank.application.commands.bulk_update_questions import BulkUpdateQuestionsHandler
from app.modules.bank.application.commands.create_question import CreateQuestionHandler
from app.modules.bank.application.commands.delete_question import DeleteQuestionHandler
from app.modules.bank.application.commands.review_question import ReviewQuestionHandler
from app.modules.bank.application.commands.update_question import UpdateQuestionHandler
from app.modules.bank.application.queries.demo_question import DemoQuestionHandler
from app.modules.bank.application.queries.document_questions import DocumentQuestionsHandler
from app.modules.bank.application.queries.get_question import GetQuestionHandler
from app.modules.bank.application.queries.get_review_document import GetReviewDocumentHandler
from app.modules.bank.application.queries.question_facets import QuestionFacetsHandler
from app.modules.bank.application.queries.review_queue import ReviewQueueHandler
from app.modules.bank.application.queries.search_flagged import SearchFlaggedHandler
from app.modules.bank.application.queries.search_questions import SearchQuestionsHandler
from app.modules.bank.application.queries.search_review_documents import SearchReviewDocumentsHandler
from app.modules.bank.domain.ports import StaffDirectory, Taxonomy
from app.modules.bank.infrastructure.adapters.sql import SqlAnswerStats, SqlReviewDocuments, SqlReviewSettings
from app.modules.bank.infrastructure.read_models import SqlQuestionReader, SqlReviewReader
from app.modules.bank.infrastructure.repositories import (
    SqlDocumentQuestions,
    SqlDuplicateFinder,
    SqlQuestionRepository,
    SqlQuestionUsage,
    SqlReviewLog,
)
from app.shared.infrastructure.db import get_db
from app.shared.infrastructure.sql_unit_of_work import SqlUnitOfWork

_taxonomy: Callable[[Session], Taxonomy] | None = None
_staff: Callable[[Session], StaffDirectory] | None = None


def register_taxonomy(factory: Callable[[Session], Taxonomy]) -> None:
    global _taxonomy
    _taxonomy = factory


def register_staff_directory(factory: Callable[[Session], StaffDirectory]) -> None:
    global _staff
    _staff = factory


class _RegisteredTaxonomy:
    """Resolves the registered taxonomy on first use (the worker's triage and key audit never need it)."""

    def __init__(self, db: Session):
        self.db = db

    def _target(self) -> Taxonomy:
        if _taxonomy is None:
            raise RuntimeError("no taxonomy registered")
        return _taxonomy(self.db)

    def topic_paths(self, org_id: uuid.UUID, topic_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        return self._target().topic_paths(org_id, topic_ids)

    def tag_groups(self, org_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        return self._target().tag_groups(org_id, tag_ids)

    def subject_exists(self, org_id: uuid.UUID, subject_id: uuid.UUID) -> bool:
        return self._target().subject_exists(org_id, subject_id)


def _staff_directory(db: Session) -> StaffDirectory:
    if _staff is None:
        raise RuntimeError("no staff directory registered")
    return _staff(db)


def bank_api(db: Session) -> BankApi:
    """The bank for another context, the worker or the bootstrap, on the caller's session."""
    return BankApi(SqlQuestionRepository(db), SqlQuestionReader(db), _RegisteredTaxonomy(db), SqlDuplicateFinder(db),
                   SqlAnswerStats(db), SqlReviewLog(db), SqlUnitOfWork(db), SqlDocumentQuestions(db))


# ------------------------------------------------------------------ questions

def search_questions(db: Session = Depends(get_db)) -> SearchQuestionsHandler:
    return SearchQuestionsHandler(SqlQuestionReader(db), _RegisteredTaxonomy(db))


def question_facets(db: Session = Depends(get_db)) -> QuestionFacetsHandler:
    return QuestionFacetsHandler(SqlQuestionReader(db), _RegisteredTaxonomy(db))


def get_question(db: Session = Depends(get_db)) -> GetQuestionHandler:
    return GetQuestionHandler(SqlQuestionRepository(db), SqlQuestionReader(db))


def demo_question(db: Session = Depends(get_db)) -> DemoQuestionHandler:
    return DemoQuestionHandler(SqlQuestionReader(db))


def create_question(db: Session = Depends(get_db)) -> CreateQuestionHandler:
    return CreateQuestionHandler(SqlQuestionRepository(db), _RegisteredTaxonomy(db), SqlReviewLog(db), SqlQuestionReader(db), SqlUnitOfWork(db))


def update_question(db: Session = Depends(get_db)) -> UpdateQuestionHandler:
    return UpdateQuestionHandler(SqlQuestionRepository(db), _RegisteredTaxonomy(db), SqlReviewLog(db), SqlReviewSettings(db),
                                 SqlQuestionReader(db), SqlUnitOfWork(db))


def delete_question(db: Session = Depends(get_db)) -> DeleteQuestionHandler:
    return DeleteQuestionHandler(SqlQuestionRepository(db), SqlQuestionUsage(db), SqlReviewLog(db), SqlUnitOfWork(db))


def bulk_update_questions(db: Session = Depends(get_db)) -> BulkUpdateQuestionsHandler:
    return BulkUpdateQuestionsHandler(SqlQuestionRepository(db), _RegisteredTaxonomy(db), SqlReviewLog(db), SqlUnitOfWork(db))


# ------------------------------------------------------------------ review

def search_review_documents(db: Session = Depends(get_db)) -> SearchReviewDocumentsHandler:
    return SearchReviewDocumentsHandler(SqlReviewReader(db))


def get_review_document(db: Session = Depends(get_db)) -> GetReviewDocumentHandler:
    return GetReviewDocumentHandler(SqlReviewReader(db))


def assign_reviewer(db: Session = Depends(get_db)) -> AssignReviewerHandler:
    return AssignReviewerHandler(SqlReviewDocuments(db), _staff_directory(db), SqlReviewReader(db), SqlUnitOfWork(db))


def review_queue(db: Session = Depends(get_db)) -> ReviewQueueHandler:
    return ReviewQueueHandler(SqlQuestionRepository(db), SqlReviewDocuments(db), SqlQuestionReader(db))


def review_question(db: Session = Depends(get_db)) -> ReviewQuestionHandler:
    return ReviewQuestionHandler(SqlQuestionRepository(db), SqlReviewLog(db), SqlReviewSettings(db), SqlQuestionReader(db), SqlUnitOfWork(db))


def apply_answer_key(db: Session = Depends(get_db)) -> ApplyAnswerKeyHandler:
    return ApplyAnswerKeyHandler(SqlQuestionRepository(db), SqlReviewDocuments(db), SqlReviewLog(db), SqlUnitOfWork(db))


def approve_confident(db: Session = Depends(get_db)) -> ApproveConfidentHandler:
    return ApproveConfidentHandler(SqlQuestionRepository(db), SqlReviewDocuments(db), SqlReviewLog(db), SqlUnitOfWork(db))


def audit_keys(db: Session = Depends(get_db)) -> AuditKeysHandler:
    return AuditKeysHandler(SqlQuestionRepository(db), SqlAnswerStats(db), SqlReviewLog(db), SqlUnitOfWork(db))


def search_flagged(db: Session = Depends(get_db)) -> SearchFlaggedHandler:
    return SearchFlaggedHandler(SqlReviewReader(db), SqlQuestionReader(db))


def document_questions(db: Session = Depends(get_db)) -> DocumentQuestionsHandler:
    return DocumentQuestionsHandler(SqlReviewDocuments(db), SqlDocumentQuestions(db), SqlQuestionReader(db))
