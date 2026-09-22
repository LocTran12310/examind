from dataclasses import dataclass
import uuid

from app.modules.assessment.application.common import exam_rows, load_assignment, students_of
from app.modules.assessment.application.ports import ResultReader
from app.modules.assessment.domain.entities import STAFF_ROLES
from app.modules.assessment.domain.ports import AssignmentRepository, ExamRepository, QuestionBank, Roster
from app.modules.assessment.domain.services.scoring import scaled
from app.shared.application.actor import Actor
from app.shared.domain.errors import Forbidden


@dataclass(frozen=True)
class AssignmentReport:
    assignment_id: uuid.UUID


class AssignmentReportHandler:
    """A teacher's view of one assignment: every targeted student (best submitted score on the exam's scale, status,
    tab switches), the average and distribution, and per question the success ratio and the most chosen wrong option."""

    def __init__(self, assignments: AssignmentRepository, exams: ExamRepository, bank: QuestionBank, roster: Roster, results: ResultReader):
        self.assignments, self.exams, self.bank, self.roster, self.results = assignments, exams, bank, roster, results

    def __call__(self, actor: Actor, query: AssignmentReport) -> dict:
        if actor.role not in STAFF_ROLES:
            raise Forbidden()
        a = load_assignment(self.assignments, actor.org_id, query.assignment_id)
        exam = self.exams.get_any(a.exam_id)
        scale_to = exam.scale_to
        targets = students_of(self.assignments, self.roster, a)
        attempts = self.results.attempts(a.id)
        by_student: dict = {}
        for t in attempts:
            by_student.setdefault(t.student_id, []).append(t)
        users = self.results.people(targets | set(by_student))
        students, scores = [], []
        for sid in sorted(targets | set(by_student), key=lambda i: users[i].full_name if i in users else ""):
            ts = by_student.get(sid, [])
            best = max((t for t in ts if t.status == "submitted"), key=lambda t: t.score or 0, default=None)
            latest = ts[-1] if ts else None
            s10 = scaled(best.score or 0, best.max_score or 0, scale_to) if best else None
            if s10 is not None:
                scores.append(s10)
            u = users.get(sid)
            students.append({"student_id": sid, "full_name": u.full_name if u else "?", "username": u.username if u else "?",
                             "status": "submitted" if best else ("in_progress" if latest else "not_started"),
                             "attempt_id": (best or latest).id if (best or latest) else None, "score10": s10,
                             "needs_grading": bool(best and best.needs_grading), "tab_switches": max((t.tab_switches for t in ts), default=0)})
        buckets = [0] * 10
        for s in scores:
            buckets[min(9, int(s // (scale_to / 10)))] += 1
        submitted_ids = [t.id for t in attempts if t.status == "submitted"]
        answers: dict = {}
        if submitted_ids:
            for ans in self.results.answers(submitted_ids):
                answers.setdefault(ans.question_id, []).append(ans)
        per_question = []
        for eq, q in exam_rows(self.exams, self.bank, a.exam_id):
            got = answers.get(q.id, [])
            graded = [x for x in got if x.points is not None]
            wrong: dict = {}
            if q.type == "mcq":
                for x in got:
                    k = (x.response or {}).get("key")
                    if k and k != (x.key_snapshot or {}).get("key"):
                        wrong[k] = wrong.get(k, 0) + 1
            top_wrong = max(wrong.items(), key=lambda kv: kv[1]) if wrong else None
            max_graded = sum(x.max_points for x in graded)
            per_question.append({"question_id": q.id, "position": eq.position, "type": q.type, "stem": q.stem[:300], "answered": len(got),
                                 "ratio": round(sum(x.points for x in graded) / max_graded, 4) if graded and max_graded else None,
                                 "top_wrong": {"label": top_wrong[0], "count": top_wrong[1]} if top_wrong else None})
        return {"assignment_id": a.id, "title": a.title, "students": students,
                "submitted": len({t.student_id for t in attempts if t.status == "submitted"}), "total_students": len(targets),
                "average": round(sum(scores) / len(scores), 2) if scores else None,
                "distribution": [{"from": i * scale_to / 10, "to": (i + 1) * scale_to / 10, "count": c} for i, c in enumerate(buckets)],
                "questions": per_question}
