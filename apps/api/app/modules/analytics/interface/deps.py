"""Builds the analytics handlers for a request (composition of ports and adapters). The classes and members (academic,
identity) and the exams and attempts (assessment) are reached through factories the composition root registers
(app/main.py, app/worker/handlers.py): analytics never imports another module."""
from collections.abc import Callable

from fastapi import Depends
from sqlalchemy.orm import Session

from app.modules.analytics.application.api import AnalyticsApi
from app.modules.analytics.application.commands.assign_class_review import AssignClassReviewHandler
from app.modules.analytics.application.commands.rebuild_mastery import RebuildMasteryHandler
from app.modules.analytics.application.commands.start_practice import StartPracticeHandler
from app.modules.analytics.application.common import PracticePlanner
from app.modules.analytics.application.ports import Roster
from app.modules.analytics.application.queries.class_overview import ClassOverviewHandler
from app.modules.analytics.application.queries.class_summary import ClassSummaryHandler
from app.modules.analytics.application.queries.group_stats import GroupStatsHandler
from app.modules.analytics.application.queries.heatmap import HeatmapHandler
from app.modules.analytics.application.queries.my_mastery import MyMasteryHandler
from app.modules.analytics.application.queries.my_practice import MyPracticeHandler
from app.modules.analytics.application.queries.student_mastery import StudentMasteryHandler
from app.modules.analytics.application.queries.topic_stats import TopicStatsHandler
from app.modules.analytics.application.queries.weekly_mastery import MyWeeklyMasteryHandler, StudentWeeklyMasteryHandler
from app.modules.analytics.domain.ports import Assessment
from app.modules.analytics.infrastructure.read_models import SqlReportReader
from app.modules.analytics.infrastructure.repositories import (
    SqlAnswerHistory,
    SqlMasteryRepository,
    SqlQuestionPool,
    SqlTopics,
    SqlWeekRepository,
)
from app.shared.domain.clock import utcnow
from app.shared.infrastructure.calendar import TzCalendar
from app.shared.infrastructure.db import get_db
from app.shared.infrastructure.sql_unit_of_work import SqlUnitOfWork

_roster: Callable[[Session], Roster] | None = None
_assessment: Callable[[Session], Assessment] | None = None


def register_roster(factory: Callable[[Session], Roster]) -> None:
    global _roster
    _roster = factory


def register_assessment(factory: Callable[[Session], Assessment]) -> None:
    global _assessment
    _assessment = factory


def _registered(factory, what: str):
    if factory is None:
        raise RuntimeError(f"no {what} registered")
    return factory


def _roster_of(db: Session) -> Roster:
    return _registered(_roster, "roster")(db)


def _assessment_of(db: Session) -> Assessment:
    return _registered(_assessment, "assessment")(db)


def analytics_api(db: Session) -> AnalyticsApi:
    """Analytics for another context, the worker or the bootstrap, on the caller's session."""
    return AnalyticsApi(SqlMasteryRepository(db), SqlTopics(db), SqlAnswerHistory(db), SqlWeekRepository(db), TzCalendar(),
                        utcnow, SqlUnitOfWork(db))


def practice_planner(db: Session) -> PracticePlanner:
    return PracticePlanner(SqlMasteryRepository(db), SqlTopics(db), SqlAnswerHistory(db), SqlQuestionPool(db), utcnow)


# ------------------------------------------------------------------ reports

def topic_stats(db: Session = Depends(get_db)) -> TopicStatsHandler:
    return TopicStatsHandler(SqlReportReader(db))


def group_stats(db: Session = Depends(get_db)) -> GroupStatsHandler:
    return GroupStatsHandler(SqlReportReader(db))


def heatmap(db: Session = Depends(get_db)) -> HeatmapHandler:
    return HeatmapHandler(SqlReportReader(db))


# ------------------------------------------------------------------ mastery and personal review

def my_mastery(db: Session = Depends(get_db)) -> MyMasteryHandler:
    return MyMasteryHandler(SqlMasteryRepository(db), SqlTopics(db), utcnow)


def student_mastery(db: Session = Depends(get_db)) -> StudentMasteryHandler:
    return StudentMasteryHandler(SqlMasteryRepository(db), SqlTopics(db), _roster_of(db), utcnow)


def class_summary(db: Session = Depends(get_db)) -> ClassSummaryHandler:
    return ClassSummaryHandler(SqlReportReader(db))


def class_overview(db: Session = Depends(get_db)) -> ClassOverviewHandler:
    return ClassOverviewHandler(SqlMasteryRepository(db), SqlTopics(db), _roster_of(db), _assessment_of(db), utcnow)


def rebuild_mastery(db: Session = Depends(get_db)) -> RebuildMasteryHandler:
    return RebuildMasteryHandler(SqlMasteryRepository(db), SqlTopics(db), SqlAnswerHistory(db), SqlUnitOfWork(db))


def my_weekly_mastery(db: Session = Depends(get_db)) -> MyWeeklyMasteryHandler:
    return MyWeeklyMasteryHandler(SqlWeekRepository(db))


def student_weekly_mastery(db: Session = Depends(get_db)) -> StudentWeeklyMasteryHandler:
    return StudentWeeklyMasteryHandler(SqlWeekRepository(db), _roster_of(db))


def start_practice(db: Session = Depends(get_db)) -> StartPracticeHandler:
    return StartPracticeHandler(practice_planner(db), _assessment_of(db), _roster_of(db), utcnow, SqlUnitOfWork(db))


def my_practice(db: Session = Depends(get_db)) -> MyPracticeHandler:
    return MyPracticeHandler(_assessment_of(db))


def assign_class_review(db: Session = Depends(get_db)) -> AssignClassReviewHandler:
    return AssignClassReviewHandler(practice_planner(db), _assessment_of(db), _roster_of(db), SqlUnitOfWork(db))
