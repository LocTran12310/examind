"""Per-org reference data: subjects, grades, semesters and the Toán topic tree (A-10, A-11)."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.metadata  # noqa: F401  (every table and mapping)
from app.modules.academic.domain.entities import Grade, SchoolLevel
from app.modules.taxonomy.domain.entities import Semester, Subject
from app.modules.taxonomy.domain.topics import Topic, topic_label
from app.seed.math_topics import MATH_TREE

SUBJECTS = [("toan", "Toán"), ("ly", "Vật lý"), ("hoa", "Hóa học"), ("sinh", "Sinh học"), ("van", "Ngữ văn"), ("anh", "Tiếng Anh")]
SEMESTERS = [("hk1", "Học kỳ 1"), ("hk2", "Học kỳ 2")]
GRADES = range(6, 13)
LEVELS = [("thcs", "Trung học cơ sở", 6, 9), ("thpt", "Trung học phổ thông", 10, 12)]  # A-01


def seed_org(db: Session, org_id: uuid.UUID) -> None:
    """Idempotent: only inserts what is missing."""
    subjects = {s.code: s for s in db.scalars(select(Subject).where(Subject.organization_id == org_id))}
    for i, (code, name) in enumerate(SUBJECTS):
        if code not in subjects:
            subjects[code] = Subject(organization_id=org_id, code=code, name=name, sort=i)
            db.add(subjects[code])
    levels = list(db.scalars(select(SchoolLevel).where(SchoolLevel.organization_id == org_id)))
    if not levels:  # seed the defaults once; afterwards the org owns its levels (A-01)
        levels = [SchoolLevel(organization_id=org_id, code=code, name=name, grade_from=lo, grade_to=hi, sort=i)
                  for i, (code, name, lo, hi) in enumerate(LEVELS)]
        db.add_all(levels)
    db.flush()
    have_grades = list(db.scalars(select(Grade).where(Grade.organization_id == org_id)))
    level_of = lambda n: next((lv for lv in levels if lv.grade_from <= n <= lv.grade_to), None)  # noqa: E731
    if not have_grades:  # first seed only: grades the org deletes later must not come back on boot
        for g in GRADES:
            lv = level_of(g)
            db.add(Grade(organization_id=org_id, level=g, name=f"Lớp {g}", school_level_id=lv.id if lv else None))
    for g in have_grades:
        if g.school_level_id is None and (lv := level_of(g.level)):
            g.school_level_id = lv.id
    have_sem = set(db.scalars(select(Semester.code).where(Semester.organization_id == org_id)))
    for i, (code, name) in enumerate(SEMESTERS):
        if code not in have_sem:
            db.add(Semester(organization_id=org_id, code=code, name=name, sort=i))
    db.flush()

    from app.modules.academic.interface.deps import academic_api

    academic = academic_api(db)
    academic.ensure_year(org_id, academic.current_code())  # every org opens with the current school year (active when none is)

    math = subjects["toan"]
    has_topics = db.scalar(select(Topic.id).where(Topic.organization_id == org_id, Topic.subject_id == math.id).limit(1))
    if not has_topics:
        _add_nodes(db, org_id, math.id, None, "", MATH_TREE)
    db.flush()


def _add_nodes(db: Session, org_id, subject_id, parent_id, parent_path: str, nodes) -> None:
    for i, (name, kind, grade, children) in enumerate(nodes):
        tid = uuid.uuid4()
        path = f"{parent_path}.{topic_label(tid)}" if parent_path else topic_label(tid)
        db.add(Topic(id=tid, organization_id=org_id, subject_id=subject_id, parent_id=parent_id,
                     name=name, level_kind=kind, grade=grade, path=path, sort=i))
        _add_nodes(db, org_id, subject_id, tid, path, children)
