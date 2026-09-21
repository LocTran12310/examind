from datetime import timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.security import now
from app.models import Assignment, AssignmentTarget, Exam
from tests.factories import make_org


def test_constraints_and_ltree_facts(db):
    org = make_org(db)
    db.commit()
    exam = Exam(organization_id=org.id, title="Đề")
    db.add(exam)
    db.flush()
    assert exam.settings["points_by_type"]["true_false"] == 1.0
    bad = Assignment(organization_id=org.id, exam_id=exam.id, title="x", open_at=now(), close_at=now() - timedelta(hours=1), duration_minutes=10)
    db.add(bad)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
    exam = Exam(organization_id=org.id, title="Đề")
    db.add(exam)
    db.flush()
    a = Assignment(organization_id=org.id, exam_id=exam.id, title="x", open_at=now(), close_at=now() + timedelta(hours=1), duration_minutes=10)
    db.add(a)
    db.flush()
    db.add(AssignmentTarget(assignment_id=a.id))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
    assert db.execute(text("select 'a.b.c'::ltree <@ 'a.b'::ltree")).scalar() is True
