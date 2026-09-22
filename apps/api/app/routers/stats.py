import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deps import OrgScope, org_scope
from app.services import stats

router = APIRouter(tags=["stats"])


def _filters(class_id, student_id, assignment_id, date_from, date_to, school_year_id=None, term_code=None):
    return {"class_id": class_id, "student_id": student_id, "assignment_id": assignment_id,
            "date_from": stats.parse_date(date_from), "date_to": stats.parse_date(date_to),
            "school_year_id": school_year_id, "term_code": term_code if term_code in ("hk1", "hk2") else None}


@router.get("/stats/topics")
def topic_stats(subject_id: uuid.UUID | None = None, class_id: uuid.UUID | None = None, student_id: uuid.UUID | None = None,
                assignment_id: uuid.UUID | None = None, date_from: str | None = None, date_to: str | None = None,
                school_year_id: uuid.UUID | None = None, term_code: str | None = None,
                scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    return stats.topics(db, scope, subject_id=subject_id,
                        **_filters(class_id, student_id, assignment_id, date_from, date_to, school_year_id, term_code))


@router.get("/stats/groups")
def group_stats(by: str = "type", class_id: uuid.UUID | None = None, student_id: uuid.UUID | None = None,
                assignment_id: uuid.UUID | None = None, date_from: str | None = None, date_to: str | None = None,
                school_year_id: uuid.UUID | None = None, term_code: str | None = None,
                scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    return stats.groups(db, scope, by, **_filters(class_id, student_id, assignment_id, date_from, date_to, school_year_id, term_code))


@router.get("/stats/heatmap")
def heatmap(class_id: uuid.UUID, level: int = 1, subject_id: uuid.UUID | None = None, term_code: str | None = None,
            scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    return stats.heatmap(db, scope, class_id, level, subject_id, term_code if term_code in ("hk1", "hk2") else None)
