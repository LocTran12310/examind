from dataclasses import dataclass
from datetime import timedelta
import uuid

from app.modules.analytics.application.common import Clock, PracticePlanner
from app.modules.analytics.application.ports import Roster
from app.modules.analytics.domain.ports import Assessment
from app.modules.analytics.domain.services.practice import PRACTICE_MINUTES, adaptive_settings, clamp_count, plan_summary
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Conflict, Forbidden


@dataclass(frozen=True)
class StartPractice:
    count: int = 20
    subject_id: uuid.UUID | None = None


class StartPracticeHandler:
    """A student asks for a practice exam (5–50 questions): planned for them, created, and an attempt started with an
    hour to finish. {attempt_id, question_count, note, groups}."""

    def __init__(self, planner: PracticePlanner, assessment: Assessment, roster: Roster, clock: Clock, uow: UnitOfWork):
        self.planner, self.assessment, self.roster, self.clock, self.uow = planner, assessment, roster, clock, uow

    def __call__(self, actor: Actor, cmd: StartPractice) -> dict:
        if actor.role != "student":
            raise Forbidden()
        plan = self.planner.build(actor.org_id, actor.user_id, clamp_count(cmd.count), cmd.subject_id)
        if not plan.picks:
            raise Conflict("Ngân hàng chưa có câu hỏi phù hợp", code="empty_bank")
        me = self.roster.person(actor.user_id)
        adaptive = adaptive_settings(actor.user_id, plan)
        exam_id = self.assessment.create_exam(actor.org_id, f"Đề ôn tập – {me.full_name if me else ''}", actor.user_id, adaptive,
                                              [p.question_id for p in plan.picks])
        attempt_id = self.assessment.start_attempt(actor.org_id, exam_id, actor.user_id, self.clock() + timedelta(minutes=PRACTICE_MINUTES))
        self.uow.commit()
        return {"attempt_id": attempt_id, "question_count": len(plan.picks), **plan_summary({"adaptive": adaptive})}
