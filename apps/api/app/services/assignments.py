"""Assignments and attempts moved to app.modules.assessment (architecture-refactor UOW-06); what the old layout
(personal practice) still calls."""
from sqlalchemy.orm import Session

from app.modules.assessment.interface.deps import assessment_api


def new_attempt(db: Session, org_id, exam_id, student_id, deadline, assignment_id=None, shuffle_q=True, shuffle_o=True):
    return assessment_api(db).new_attempt(org_id, exam_id, student_id, deadline, assignment_id, shuffle_q, shuffle_o)
