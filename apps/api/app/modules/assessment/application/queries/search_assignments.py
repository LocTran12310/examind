from dataclasses import dataclass

from app.modules.assessment.application.common import students_of
from app.modules.assessment.application.dto import AssignmentView
from app.modules.assessment.application.ports import AssignmentReader
from app.modules.assessment.domain.ports import AssignmentRepository, Roster
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchAssignments:
    request: SearchRequest


class SearchAssignmentsHandler:
    """Each row with its number of targeted students, of students who submitted, and the target classes."""

    def __init__(self, reader: AssignmentReader, assignments: AssignmentRepository, roster: Roster):
        self.reader, self.assignments, self.roster = reader, assignments, roster

    def __call__(self, actor: Actor, query: SearchAssignments) -> Page[AssignmentView]:
        page = self.reader.search(actor.org_id, query.request)
        rows = [AssignmentView(r.assignment, len(students_of(self.assignments, self.roster, r.assignment)), r.submitted, r.classes)
                for r in page.data]
        return Page(rows, page.total, page.page, page.limit)
