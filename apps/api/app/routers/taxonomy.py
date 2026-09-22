from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deps import OrgScope, org_scope
from app.models import Grade, SchoolLevel, Semester, Subject
from app.schemas.taxonomy import GradeOut, SemesterOut, SubjectOut, TaxonomyOut

router = APIRouter(tags=["taxonomy"])


@router.get("/taxonomy", response_model=TaxonomyOut)
def taxonomy(scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    o = scope.org_id
    return TaxonomyOut(
        subjects=[SubjectOut(id=s.id, code=s.code, name=s.name) for s in db.scalars(select(Subject).where(Subject.organization_id == o).order_by(Subject.sort))],
        grades=[GradeOut(id=g.id, level=g.level, name=g.name, school_level_id=g.school_level_id, school_level_name=lv_name)
                for g, lv_name in db.execute(select(Grade, SchoolLevel.name).outerjoin(SchoolLevel, SchoolLevel.id == Grade.school_level_id)
                                             .where(Grade.organization_id == o).order_by(Grade.level))],
        semesters=[SemesterOut(id=s.id, code=s.code, name=s.name) for s in db.scalars(select(Semester).where(Semester.organization_id == o).order_by(Semester.sort))],
    )
