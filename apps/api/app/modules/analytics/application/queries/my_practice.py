from app.modules.analytics.domain.ports import Assessment
from app.modules.analytics.domain.services.practice import plan_summary
from app.shared.application.actor import Actor
from app.shared.domain.errors import Forbidden

HISTORY = 20


class MyPracticeHandler:
    """A student's last practice attempts with their score and why the questions were chosen."""

    def __init__(self, assessment: Assessment):
        self.assessment = assessment

    def __call__(self, actor: Actor) -> list[dict]:
        if actor.role != "student":
            raise Forbidden()
        return [{"attempt_id": a.attempt_id, "title": a.title, "status": a.status, "started_at": a.started_at, "submitted_at": a.submitted_at,
                 "score10": a.score10, **plan_summary(a.settings)} for a in self.assessment.practice_attempts(actor.org_id, actor.user_id, HISTORY)]
