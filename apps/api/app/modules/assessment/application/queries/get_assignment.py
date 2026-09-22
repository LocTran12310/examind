from dataclasses import dataclass
import uuid

from app.modules.assessment.application.common import load_assignment, students_of
from app.modules.assessment.application.dto import AssignmentView
from app.modules.assessment.domain.ports import AssignmentRepository, Roster
from app.shared.application.actor import Actor


@dataclass(frozen=True)
class GetAssignment:
    assignment_id: uuid.UUID


class GetAssignmentHandler:
    def __init__(self, assignments: AssignmentRepository, roster: Roster):
        self.assignments, self.roster = assignments, roster

    def __call__(self, actor: Actor, query: GetAssignment) -> AssignmentView:
        a = load_assignment(self.assignments, actor.org_id, query.assignment_id)
        return AssignmentView(a, students=len(students_of(self.assignments, self.roster, a)))
