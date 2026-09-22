from app.modules.assessment.application.common import Clock
from app.modules.assessment.application.dto import MyAssignmentView, attempt_brief
from app.modules.assessment.domain.ports import AssignmentRepository, AttemptRepository, Roster
from app.modules.assessment.domain.services import assignment_rules
from app.shared.application.actor import Actor
from app.shared.domain.errors import Forbidden


class MyAssignmentsHandler:
    """A student's home: what was given to them or their classes, the window state, their attempts (scores once
    submitted) and the attempts left."""

    def __init__(self, assignments: AssignmentRepository, attempts: AttemptRepository, roster: Roster, clock: Clock):
        self.assignments, self.attempts, self.roster, self.clock = assignments, attempts, roster, clock

    def __call__(self, actor: Actor) -> list[MyAssignmentView]:
        if actor.role != "student":
            raise Forbidden()
        now = self.clock()
        out = []
        for a in self.assignments.for_student(actor.org_id, actor.user_id, self.roster.classes_of(actor.org_id, actor.user_id)):
            attempts = self.attempts.of_student(a.id, actor.user_id)
            out.append(MyAssignmentView(
                a, assignment_rules.window_state(a, now),
                [attempt_brief(t, assignment_rules.results_visible(a, t, now, score_only=True)) for t in attempts],
                assignment_rules.attempts_left(a, len(attempts))))
        return out
