import uuid

from fastapi import APIRouter, Depends

from app.modules.analytics.application.commands.assign_class_review import AssignClassReview, AssignClassReviewHandler
from app.modules.analytics.application.commands.rebuild_mastery import RebuildMastery, RebuildMasteryHandler
from app.modules.analytics.application.commands.start_practice import StartPractice, StartPracticeHandler
from app.modules.analytics.application.dto import ReportFilters
from app.modules.analytics.application.queries.class_overview import ClassOverview, ClassOverviewHandler
from app.modules.analytics.application.queries.class_summary import ClassSummary, ClassSummaryHandler
from app.modules.analytics.application.queries.group_stats import GroupStats, GroupStatsHandler
from app.modules.analytics.application.queries.heatmap import Heatmap, HeatmapHandler
from app.modules.analytics.application.queries.my_mastery import MyMasteryHandler
from app.modules.analytics.application.queries.my_practice import MyPracticeHandler
from app.modules.analytics.application.queries.student_mastery import StudentMastery, StudentMasteryHandler
from app.modules.analytics.application.queries.topic_stats import TopicStats, TopicStatsHandler
from app.modules.analytics.application.queries.weekly_mastery import (
    MyWeeklyMasteryHandler,
    StudentWeeklyMastery,
    StudentWeeklyMasteryHandler,
)
from app.modules.analytics.domain.services.reports import term
from app.modules.analytics.interface import deps
from app.modules.analytics.interface.schemas import ClassAdaptiveIn, PracticeIn, report_filters
from app.shared.application.actor import Actor
from app.shared.interface.auth import current_actor, staff_actor

router = APIRouter(tags=["analytics"])


# ------------------------------------------------------------------ reports over the answer facts

@router.get("/stats/topics")
def topic_stats(subject_id: uuid.UUID | None = None, filters: ReportFilters = Depends(report_filters),
                actor: Actor = Depends(current_actor), handle: TopicStatsHandler = Depends(deps.topic_stats)):
    """Per topic, summed up the tree; students see their own answers only."""
    return handle(actor, TopicStats(filters, subject_id))


@router.get("/stats/groups")
def group_stats(by: str = "type", filters: ReportFilters = Depends(report_filters), actor: Actor = Depends(current_actor),
                handle: GroupStatsHandler = Depends(deps.group_stats)):
    """Per question type, difficulty or tag, weakest first."""
    return handle(actor, GroupStats(by, filters))


@router.get("/stats/heatmap")
def heatmap(class_id: uuid.UUID, level: int = 1, subject_id: uuid.UUID | None = None, term_code: str | None = None,
            actor: Actor = Depends(current_actor), handle: HeatmapHandler = Depends(deps.heatmap)):
    return handle(actor, Heatmap(class_id, level, subject_id, term(term_code)))


# ------------------------------------------------------------------ mastery

@router.get("/me/mastery")
def my_mastery(actor: Actor = Depends(current_actor), handle: MyMasteryHandler = Depends(deps.my_mastery)):
    return handle(actor)


@router.get("/students/{student_id}/mastery")
def student_mastery(student_id: uuid.UUID, actor: Actor = Depends(staff_actor),
                    handle: StudentMasteryHandler = Depends(deps.student_mastery)):
    return handle(actor, StudentMastery(student_id))


@router.get("/me/mastery/weekly")
def my_weekly_mastery(actor: Actor = Depends(current_actor), handle: MyWeeklyMasteryHandler = Depends(deps.my_weekly_mastery)):
    """The student's own weekly snapshots, oldest week first."""
    return handle(actor)


@router.get("/students/{student_id}/mastery/weekly")
def student_weekly_mastery(student_id: uuid.UUID, actor: Actor = Depends(staff_actor),
                           handle: StudentWeeklyMasteryHandler = Depends(deps.student_weekly_mastery)):
    return handle(actor, StudentWeeklyMastery(student_id))


@router.post("/analytics/mastery/rebuild")
def rebuild_mastery(actor: Actor = Depends(current_actor), handle: RebuildMasteryHandler = Depends(deps.rebuild_mastery)):
    """An org admin replays their organisation's answer facts: {students, topics, facts}."""
    return vars(handle(actor, RebuildMastery()))


@router.get("/classes/{class_id}/summary")
def class_summary(class_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: ClassSummaryHandler = Depends(deps.class_summary)):
    """Cả lớp trong một lời gọi: số bài giao, số lượt đã nộp, điểm trung bình trên thang 10 theo tỉ lệ đúng, phổ
    điểm mười cột, và năm chuyên đề lớp yếu nhất. Lớp chưa ai nộp trả `average: null` và phổ điểm toàn 0 — rỗng
    có cấu trúc, để màn hình phân biệt được "chưa đo" với "đo rồi và bằng 0"."""
    return handle(actor, ClassSummary(class_id))


@router.get("/classes/{class_id}/overview")
def class_overview(class_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: ClassOverviewHandler = Depends(deps.class_overview)):
    return handle(actor, ClassOverview(class_id))


# ------------------------------------------------------------------ personal review exams

@router.post("/me/practice")
def start_practice(body: PracticeIn, actor: Actor = Depends(current_actor), handle: StartPracticeHandler = Depends(deps.start_practice)):
    return handle(actor, StartPractice(body.count, body.subject_id))


@router.get("/me/practice")
def my_practice(actor: Actor = Depends(current_actor), handle: MyPracticeHandler = Depends(deps.my_practice)):
    """The last 20 practice attempts (a plain list, like /me/assignments)."""
    return handle(actor)


@router.post("/classes/{class_id}/adaptive-assignments")
def class_adaptive(class_id: uuid.UUID, body: ClassAdaptiveIn, actor: Actor = Depends(staff_actor),
                   handle: AssignClassReviewHandler = Depends(deps.assign_class_review)):
    return {"created": handle(actor, AssignClassReview(class_id, body.open_at, body.close_at, body.count, body.duration_minutes, body.title))}
