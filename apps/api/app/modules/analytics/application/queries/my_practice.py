from app.modules.analytics.domain.ports import Assessment
from app.modules.analytics.domain.services.practice import plan_summary
from app.shared.application.actor import Actor

HISTORY = 20


class MyPracticeHandler:
    """The caller's last practice attempts with their score and why the questions were chosen. Roles nest
    (exam-runner-and-roles ADR-02), so staff are answered about themselves — starting one is still theirs alone."""

    def __init__(self, assessment: Assessment):
        self.assessment = assessment

    def __call__(self, actor: Actor) -> list[dict]:
        return [{"attempt_id": a.attempt_id, "title": a.title, "status": a.status, "started_at": a.started_at, "submitted_at": a.submitted_at,
                 "score10": a.score10, **plan_summary(a.settings)} for a in self.assessment.practice_attempts(actor.org_id, actor.user_id, HISTORY)]
