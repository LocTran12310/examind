from dataclasses import dataclass
from datetime import datetime
import uuid

from app.modules.analytics.application.common import PracticePlanner
from app.modules.analytics.application.ports import Roster
from app.modules.analytics.domain.ports import Assessment
from app.modules.analytics.domain.services.practice import adaptive_settings, check_window, clamp_count
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class AssignClassReview:
    class_id: uuid.UUID
    open_at: datetime
    close_at: datetime
    count: int = 15
    duration_minutes: int = 30
    title: str | None = None


class AssignClassReviewHandler:
    """A teacher gives every active student of a class their own review exam (one attempt, results after submitting);
    students the bank has nothing for are skipped. The number of exams created."""

    def __init__(self, planner: PracticePlanner, assessment: Assessment, roster: Roster, uow: UnitOfWork):
        self.planner, self.assessment, self.roster, self.uow = planner, assessment, roster, uow

    def __call__(self, actor: Actor, cmd: AssignClassReview) -> int:
        check_window(cmd.open_at, cmd.close_at, cmd.duration_minutes)
        count = clamp_count(cmd.count)
        created = 0
        for u in self.roster.class_members(actor, cmd.class_id):
            if u.role != "student" or not u.is_active:
                continue
            plan = self.planner.build(actor.org_id, u.id, count)
            if not plan.picks:
                continue
            exam_id = self.assessment.create_exam(actor.org_id, cmd.title or f"Đề ôn cá nhân – {u.full_name}", actor.user_id,
                                                  adaptive_settings(u.id, plan), [p.question_id for p in plan.picks])
            self.assessment.assign(actor.org_id, exam_id, u.id, cmd.title or "Đề ôn cá nhân", cmd.open_at, cmd.close_at,
                                   cmd.duration_minutes, actor.user_id)
            created += 1
        self.uow.commit()
        return created
