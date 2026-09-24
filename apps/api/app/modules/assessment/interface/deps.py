"""Builds the assessment handlers for a request (composition of ports and adapters). The bank, the academic and
identity contexts, the taxonomy and analytics are reached through factories the composition root registers
(app/main.py, app/worker/handlers.py): assessment never imports another module."""
from collections.abc import Callable

from fastapi import Depends
from sqlalchemy.orm import Session

from app.modules.assessment.application.api import AssessmentApi
from app.modules.assessment.application.commands.add_exam_questions import AddExamQuestionsHandler
from app.modules.assessment.application.commands.apply_blueprint import ApplyBlueprintHandler
from app.modules.assessment.application.commands.create_assignment import CreateAssignmentHandler
from app.modules.assessment.application.commands.create_exam import CreateExamHandler
from app.modules.assessment.application.commands.delete_assignment import DeleteAssignmentHandler
from app.modules.assessment.application.commands.delete_exam import DeleteExamHandler
from app.modules.assessment.application.commands.grade_essay import GradeEssayHandler
from app.modules.assessment.application.commands.record_tab_switch import RecordTabSwitchHandler
from app.modules.assessment.application.commands.remove_exam_question import RemoveExamQuestionHandler
from app.modules.assessment.application.commands.reorder_exam_questions import ReorderExamQuestionsHandler
from app.modules.assessment.application.commands.save_answer import SaveAnswerHandler
from app.modules.assessment.application.commands.set_question_points import SetQuestionPointsHandler
from app.modules.assessment.application.commands.start_attempt import StartAttemptHandler
from app.modules.assessment.application.commands.submit_attempt import SubmitAttemptHandler
from app.modules.assessment.application.commands.swap_exam_question import SwapExamQuestionHandler
from app.modules.assessment.application.commands.update_assignment import UpdateAssignmentHandler
from app.modules.assessment.application.commands.update_exam import UpdateExamHandler
from app.modules.assessment.application.common import Grading
from app.modules.assessment.application.queries.assignment_paper import AssignmentPaperHandler
from app.modules.assessment.application.queries.assignment_report import AssignmentReportHandler
from app.modules.assessment.application.queries.attempt_result import AttemptResultHandler
from app.modules.assessment.application.queries.get_assignment import GetAssignmentHandler
from app.modules.assessment.application.queries.get_attempt import GetAttemptHandler
from app.modules.assessment.application.queries.get_exam import GetExamHandler
from app.modules.assessment.application.queries.my_assignments import MyAssignmentsHandler
from app.modules.assessment.application.queries.search_assignments import SearchAssignmentsHandler
from app.modules.assessment.application.queries.search_exam_questions import SearchExamQuestionsHandler
from app.modules.assessment.application.queries.search_exams import SearchExamsHandler
from app.modules.assessment.application.queries.trial_run import TrialRunHandler
from app.modules.assessment.domain.ports import FactListener, QuestionBank, Roster, Subjects
from app.modules.assessment.infrastructure.read_models import SqlAssignmentReader, SqlExamReader, SqlPersonalReader, SqlResultReader
from app.modules.assessment.infrastructure.repositories import (
    SqlAnswerFacts,
    SqlAssignmentRepository,
    SqlAttemptRepository,
    SqlExamRepository,
)
from app.shared.domain.clock import utcnow
from app.shared.infrastructure.db import get_db
from app.shared.infrastructure.sql_unit_of_work import SqlUnitOfWork

_bank: Callable[[Session], QuestionBank] | None = None
_roster: Callable[[Session], Roster] | None = None
_subjects: Callable[[Session], Subjects] | None = None
_facts: Callable[[Session], FactListener] | None = None


def register_bank(factory: Callable[[Session], QuestionBank]) -> None:
    global _bank
    _bank = factory


def register_roster(factory: Callable[[Session], Roster]) -> None:
    global _roster
    _roster = factory


def register_subjects(factory: Callable[[Session], Subjects]) -> None:
    global _subjects
    _subjects = factory


def register_fact_listener(factory: Callable[[Session], FactListener]) -> None:
    global _facts
    _facts = factory


def _registered(factory, what: str):
    if factory is None:
        raise RuntimeError(f"no {what} registered")
    return factory


def _bank_of(db: Session) -> QuestionBank:
    return _registered(_bank, "question bank")(db)


def _roster_of(db: Session) -> Roster:
    return _registered(_roster, "roster")(db)


def grading(db: Session) -> Grading:
    return Grading(SqlAttemptRepository(db), SqlExamRepository(db), _bank_of(db), _roster_of(db), SqlAnswerFacts(db),
                   _registered(_facts, "answer fact listener")(db), utcnow)


def assessment_api(db: Session) -> AssessmentApi:
    """Assessment for another context or the worker, on the caller's session."""
    return AssessmentApi(SqlExamRepository(db), SqlAttemptRepository(db), SqlAssignmentRepository(db), _bank_of(db),
                         _registered(_subjects, "subjects")(db), grading(db), SqlPersonalReader(db), utcnow, SqlUnitOfWork(db))


# ------------------------------------------------------------------ exams

def search_exams(db: Session = Depends(get_db)) -> SearchExamsHandler:
    return SearchExamsHandler(SqlExamReader(db))


def get_exam(db: Session = Depends(get_db)) -> GetExamHandler:
    return GetExamHandler(SqlExamRepository(db), _bank_of(db))


def search_exam_questions(db: Session = Depends(get_db)) -> SearchExamQuestionsHandler:
    return SearchExamQuestionsHandler(SqlExamRepository(db), SqlExamReader(db), _bank_of(db))


def create_exam(db: Session = Depends(get_db)) -> CreateExamHandler:
    return CreateExamHandler(SqlExamRepository(db), _registered(_subjects, "subjects")(db), SqlUnitOfWork(db))


def update_exam(db: Session = Depends(get_db)) -> UpdateExamHandler:
    return UpdateExamHandler(SqlExamRepository(db), _bank_of(db), SqlUnitOfWork(db))


def delete_exam(db: Session = Depends(get_db)) -> DeleteExamHandler:
    return DeleteExamHandler(SqlExamRepository(db), SqlUnitOfWork(db))


def apply_blueprint(db: Session = Depends(get_db)) -> ApplyBlueprintHandler:
    return ApplyBlueprintHandler(SqlExamRepository(db), _bank_of(db), _registered(_subjects, "subjects")(db), SqlUnitOfWork(db))


def add_exam_questions(db: Session = Depends(get_db)) -> AddExamQuestionsHandler:
    return AddExamQuestionsHandler(SqlExamRepository(db), _bank_of(db), SqlUnitOfWork(db))


def remove_exam_question(db: Session = Depends(get_db)) -> RemoveExamQuestionHandler:
    return RemoveExamQuestionHandler(SqlExamRepository(db), SqlUnitOfWork(db))


def reorder_exam_questions(db: Session = Depends(get_db)) -> ReorderExamQuestionsHandler:
    return ReorderExamQuestionsHandler(SqlExamRepository(db), SqlUnitOfWork(db))


def swap_exam_question(db: Session = Depends(get_db)) -> SwapExamQuestionHandler:
    return SwapExamQuestionHandler(SqlExamRepository(db), _bank_of(db), SqlUnitOfWork(db))


def set_question_points(db: Session = Depends(get_db)) -> SetQuestionPointsHandler:
    return SetQuestionPointsHandler(SqlExamRepository(db), SqlUnitOfWork(db))


# ------------------------------------------------------------------ assignments

def search_assignments(db: Session = Depends(get_db)) -> SearchAssignmentsHandler:
    return SearchAssignmentsHandler(SqlAssignmentReader(db), SqlAssignmentRepository(db), _roster_of(db))


def get_assignment(db: Session = Depends(get_db)) -> GetAssignmentHandler:
    return GetAssignmentHandler(SqlAssignmentRepository(db), _roster_of(db))


def create_assignment(db: Session = Depends(get_db)) -> CreateAssignmentHandler:
    return CreateAssignmentHandler(SqlExamRepository(db), SqlAssignmentRepository(db), _roster_of(db), SqlUnitOfWork(db))


def update_assignment(db: Session = Depends(get_db)) -> UpdateAssignmentHandler:
    return UpdateAssignmentHandler(SqlAssignmentRepository(db), SqlUnitOfWork(db))


def delete_assignment(db: Session = Depends(get_db)) -> DeleteAssignmentHandler:
    return DeleteAssignmentHandler(SqlAssignmentRepository(db), SqlAttemptRepository(db), SqlUnitOfWork(db))


def my_assignments(db: Session = Depends(get_db)) -> MyAssignmentsHandler:
    return MyAssignmentsHandler(SqlAssignmentRepository(db), SqlAttemptRepository(db), _roster_of(db), utcnow)


def assignment_paper(db: Session = Depends(get_db)) -> AssignmentPaperHandler:
    """No UnitOfWork on purpose: a trial run has nothing to commit (exam-runner ADR-01)."""
    return AssignmentPaperHandler(SqlAssignmentRepository(db), SqlExamRepository(db), _bank_of(db))


def assignment_trial(db: Session = Depends(get_db)) -> TrialRunHandler:
    """No UnitOfWork either: a trial run grades in memory and has nothing to write (exam-runner ADR-01)."""
    return TrialRunHandler(SqlAssignmentRepository(db), SqlExamRepository(db), _bank_of(db), utcnow)


def assignment_report(db: Session = Depends(get_db)) -> AssignmentReportHandler:
    return AssignmentReportHandler(SqlAssignmentRepository(db), SqlExamRepository(db), _bank_of(db), _roster_of(db), SqlResultReader(db))


def start_attempt(db: Session = Depends(get_db)) -> StartAttemptHandler:
    return StartAttemptHandler(SqlAssignmentRepository(db), SqlAttemptRepository(db), SqlExamRepository(db), _bank_of(db), _roster_of(db),
                               grading(db), utcnow, SqlUnitOfWork(db))


# ------------------------------------------------------------------ attempts

def get_attempt(db: Session = Depends(get_db)) -> GetAttemptHandler:
    return GetAttemptHandler(SqlAttemptRepository(db), SqlAssignmentRepository(db), SqlExamRepository(db), grading(db), SqlResultReader(db),
                             utcnow, SqlUnitOfWork(db))


def save_answer(db: Session = Depends(get_db)) -> SaveAnswerHandler:
    return SaveAnswerHandler(SqlAttemptRepository(db), _bank_of(db), grading(db), utcnow, SqlUnitOfWork(db))


def submit_attempt(db: Session = Depends(get_db)) -> SubmitAttemptHandler:
    return SubmitAttemptHandler(SqlAttemptRepository(db), grading(db), utcnow, SqlUnitOfWork(db))


def record_tab_switch(db: Session = Depends(get_db)) -> RecordTabSwitchHandler:
    return RecordTabSwitchHandler(SqlAttemptRepository(db), SqlUnitOfWork(db))


def attempt_result(db: Session = Depends(get_db)) -> AttemptResultHandler:
    return AttemptResultHandler(SqlAttemptRepository(db), SqlAssignmentRepository(db), SqlExamRepository(db), _bank_of(db), grading(db),
                                utcnow, SqlUnitOfWork(db))


def grade_essay(db: Session = Depends(get_db)) -> GradeEssayHandler:
    return GradeEssayHandler(SqlAttemptRepository(db), _bank_of(db), grading(db), SqlUnitOfWork(db))
