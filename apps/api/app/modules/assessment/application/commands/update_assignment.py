from dataclasses import dataclass, field
import uuid

from app.modules.assessment.application.common import load_assignment
from app.modules.assessment.domain.entities import Assignment
from app.modules.assessment.domain.ports import AssignmentRepository
from app.modules.assessment.domain.services import assignment_rules
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork

FIELDS = ("title", "open_at", "close_at", "duration_minutes", "max_attempts", "shuffle_questions", "shuffle_options", "results_policy")


@dataclass(frozen=True)
class UpdateAssignment:
    assignment_id: uuid.UUID
    changes: dict = field(default_factory=dict)  # the fields sent; None leaves a field as it is


class UpdateAssignmentHandler:
    """A teacher moves the window (e.g. closes early) or changes the rules; the result must still be a valid window."""

    def __init__(self, assignments: AssignmentRepository, uow: UnitOfWork):
        self.assignments, self.uow = assignments, uow

    def __call__(self, actor: Actor, cmd: UpdateAssignment) -> Assignment:
        a = load_assignment(self.assignments, actor.org_id, cmd.assignment_id)
        given = {k: v for k, v in cmd.changes.items() if v is not None}
        merged = {"open_at": a.open_at, "close_at": a.close_at, "duration_minutes": a.duration_minutes, "max_attempts": a.max_attempts,
                  "results_policy": a.results_policy, **given}
        assignment_rules.check_window(merged["open_at"], merged["close_at"], merged["duration_minutes"], merged["max_attempts"],
                                      merged["results_policy"])
        for k in FIELDS:
            if given.get(k) is not None:
                setattr(a, k, given[k])
        self.uow.commit()
        return a
