from app.modules.assessment.application.common import Clock
from app.modules.assessment.application.dto import MyAssignmentView, attempt_brief
from app.modules.assessment.domain.ports import AssignmentRepository, AttemptRepository, ExamRepository, Roster
from app.modules.assessment.domain.services import assignment_rules
from app.shared.application.actor import Actor


class MyAssignmentsHandler:
    """A student's home: what was given to them or their classes, the window state, their attempts (scores once
    submitted) and the attempts left. Open to any member of the org, not only a student (exam-runner ADR-02): what
    keeps it the caller's own is the filter on actor.user_id below, so staff see their own — usually nothing."""

    def __init__(self, assignments: AssignmentRepository, attempts: AttemptRepository, exams: ExamRepository, roster: Roster, clock: Clock):
        self.assignments, self.attempts, self.exams, self.roster, self.clock = assignments, attempts, exams, roster, clock

    def __call__(self, actor: Actor) -> list[MyAssignmentView]:
        now = self.clock()
        given = list(self.assignments.for_student(actor.org_id, actor.user_id, self.roster.classes_of(actor.org_id, actor.user_id)))
        # one lookup for every exam behind the list: the home screen groups by subject, and asking per assignment
        # would be an N+1 on the first page anybody opens
        subjects = self.exams.subjects_of([a.exam_id for a in given])
        out = []
        for a in given:
            attempts = self.attempts.of_student(a.id, actor.user_id)
            out.append(MyAssignmentView(
                a, assignment_rules.window_state(a, now),
                [attempt_brief(t, assignment_rules.results_visible(a, t, now, score_only=True)) for t in attempts],
                assignment_rules.attempts_left(a, len(attempts)), subjects.get(a.exam_id)))
        return out
