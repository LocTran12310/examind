"""Builds the academic handlers for a request (composition of ports and adapters)."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.modules.academic.application.api import AcademicApi
from app.modules.academic.application.commands.add_members import AddMembersHandler
from app.modules.academic.application.commands.change_year_status import ChangeYearStatusHandler
from app.modules.academic.application.commands.commit_rollover import CommitRolloverHandler
from app.modules.academic.application.commands.create_class import CreateClassHandler
from app.modules.academic.application.commands.create_grade import CreateGradeHandler
from app.modules.academic.application.commands.create_level import CreateLevelHandler
from app.modules.academic.application.commands.create_year import CreateYearHandler
from app.modules.academic.application.commands.delete_class import DeleteClassHandler
from app.modules.academic.application.commands.delete_grade import DeleteGradeHandler
from app.modules.academic.application.commands.delete_level import DeleteLevelHandler
from app.modules.academic.application.commands.delete_year import DeleteYearHandler
from app.modules.academic.application.commands.remove_member import RemoveMemberHandler
from app.modules.academic.application.commands.update_class import UpdateClassHandler
from app.modules.academic.application.commands.update_grade import UpdateGradeHandler
from app.modules.academic.application.commands.update_level import UpdateLevelHandler
from app.modules.academic.application.commands.update_year import UpdateYearHandler
from app.modules.academic.application.queries.get_class import GetClassHandler
from app.modules.academic.application.queries.get_year import GetYearHandler
from app.modules.academic.application.queries.preview_rollover import PreviewRolloverHandler
from app.modules.academic.application.queries.search_classes import SearchClassesHandler
from app.modules.academic.application.queries.search_grades import SearchGradesHandler
from app.modules.academic.application.queries.search_levels import SearchLevelsHandler
from app.modules.academic.application.queries.search_years import SearchYearsHandler
from app.modules.academic.application.queries.structure_tree import StructureTreeHandler
from app.modules.academic.application.queries.student_record import StudentRecordHandler
from app.modules.academic.infrastructure.read_models import (
    SqlClassReader,
    SqlGradeReader,
    SqlLevelReader,
    SqlRecordReader,
    SqlStructureReader,
    SqlYearReader,
)
from app.modules.academic.infrastructure.repositories import (
    SqlClassRepository,
    SqlGradeRepository,
    SqlLevelRepository,
    SqlMemberDirectory,
    SqlSchoolYearRepository,
)
from app.shared.infrastructure.calendar import TzCalendar
from app.shared.infrastructure.db import get_db
from app.shared.infrastructure.sql_audit import SqlAuditTrail
from app.shared.infrastructure.sql_unit_of_work import SqlUnitOfWork


def academic_api(db: Session) -> AcademicApi:
    """The academic context for another context, the seeds or the tests, on the caller's session."""
    return AcademicApi(SqlSchoolYearRepository(db), SqlClassRepository(db), SqlGradeRepository(db), SqlAuditTrail(db), TzCalendar())


# ------------------------------------------------------------------ school years

def search_years(db: Session = Depends(get_db)) -> SearchYearsHandler:
    return SearchYearsHandler(SqlYearReader(db))


def get_year(db: Session = Depends(get_db)) -> GetYearHandler:
    return GetYearHandler(SqlSchoolYearRepository(db))


def create_year(db: Session = Depends(get_db)) -> CreateYearHandler:
    return CreateYearHandler(SqlSchoolYearRepository(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def update_year(db: Session = Depends(get_db)) -> UpdateYearHandler:
    return UpdateYearHandler(SqlSchoolYearRepository(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def change_year_status(db: Session = Depends(get_db)) -> ChangeYearStatusHandler:
    return ChangeYearStatusHandler(SqlSchoolYearRepository(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def delete_year(db: Session = Depends(get_db)) -> DeleteYearHandler:
    return DeleteYearHandler(SqlSchoolYearRepository(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def preview_rollover(db: Session = Depends(get_db)) -> PreviewRolloverHandler:
    return PreviewRolloverHandler(SqlSchoolYearRepository(db), SqlClassRepository(db), SqlGradeRepository(db), SqlClassReader(db),
                                  SqlMemberDirectory(db))


def commit_rollover(db: Session = Depends(get_db)) -> CommitRolloverHandler:
    return CommitRolloverHandler(SqlSchoolYearRepository(db), SqlClassRepository(db), SqlGradeRepository(db), SqlAuditTrail(db),
                                 TzCalendar(), SqlUnitOfWork(db))


# ------------------------------------------------------------------ classes

def search_classes(db: Session = Depends(get_db)) -> SearchClassesHandler:
    return SearchClassesHandler(SqlClassReader(db))


def get_class(db: Session = Depends(get_db)) -> GetClassHandler:
    return GetClassHandler(SqlClassRepository(db), SqlClassReader(db))


def create_class(db: Session = Depends(get_db)) -> CreateClassHandler:
    return CreateClassHandler(SqlSchoolYearRepository(db), SqlClassRepository(db), SqlGradeRepository(db), SqlAuditTrail(db),
                              TzCalendar(), SqlUnitOfWork(db))


def update_class(db: Session = Depends(get_db)) -> UpdateClassHandler:
    return UpdateClassHandler(SqlSchoolYearRepository(db), SqlClassRepository(db), SqlGradeRepository(db), SqlAuditTrail(db),
                              TzCalendar(), SqlUnitOfWork(db))


def delete_class(db: Session = Depends(get_db)) -> DeleteClassHandler:
    return DeleteClassHandler(SqlSchoolYearRepository(db), SqlClassRepository(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def add_members(db: Session = Depends(get_db)) -> AddMembersHandler:
    return AddMembersHandler(SqlSchoolYearRepository(db), SqlClassRepository(db), SqlMemberDirectory(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def remove_member(db: Session = Depends(get_db)) -> RemoveMemberHandler:
    return RemoveMemberHandler(SqlSchoolYearRepository(db), SqlClassRepository(db), SqlAuditTrail(db), SqlUnitOfWork(db))


# ------------------------------------------------------------------ structure

def structure_tree(db: Session = Depends(get_db)) -> StructureTreeHandler:
    return StructureTreeHandler(SqlStructureReader(db))


def search_levels(db: Session = Depends(get_db)) -> SearchLevelsHandler:
    return SearchLevelsHandler(SqlLevelReader(db))


def create_level(db: Session = Depends(get_db)) -> CreateLevelHandler:
    return CreateLevelHandler(SqlLevelRepository(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def update_level(db: Session = Depends(get_db)) -> UpdateLevelHandler:
    return UpdateLevelHandler(SqlLevelRepository(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def delete_level(db: Session = Depends(get_db)) -> DeleteLevelHandler:
    return DeleteLevelHandler(SqlLevelRepository(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def search_grades(db: Session = Depends(get_db)) -> SearchGradesHandler:
    return SearchGradesHandler(SqlGradeReader(db))


def create_grade(db: Session = Depends(get_db)) -> CreateGradeHandler:
    return CreateGradeHandler(SqlLevelRepository(db), SqlGradeRepository(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def update_grade(db: Session = Depends(get_db)) -> UpdateGradeHandler:
    return UpdateGradeHandler(SqlLevelRepository(db), SqlGradeRepository(db), SqlClassRepository(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def delete_grade(db: Session = Depends(get_db)) -> DeleteGradeHandler:
    return DeleteGradeHandler(SqlGradeRepository(db), SqlAuditTrail(db), SqlUnitOfWork(db))


# ------------------------------------------------------------------ students

def student_record(db: Session = Depends(get_db)) -> StudentRecordHandler:
    return StudentRecordHandler(SqlMemberDirectory(db), SqlRecordReader(db))
