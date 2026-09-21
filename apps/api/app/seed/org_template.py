"""Per-org reference data: subjects, grades, semesters and the Toán topic tree (A-10, A-11)."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.taxonomy import Grade, Semester, Subject, Topic, topic_label
from app.seed.math_topics import MATH_TREE

SUBJECTS = [("toan", "Toán"), ("ly", "Vật lý"), ("hoa", "Hóa học"), ("sinh", "Sinh học"), ("van", "Ngữ văn"), ("anh", "Tiếng Anh")]
SEMESTERS = [("hk1", "Học kỳ 1"), ("hk2", "Học kỳ 2")]
GRADES = range(6, 13)


def seed_org(db: Session, org_id: uuid.UUID) -> None:
    """Idempotent: only inserts what is missing."""
    subjects = {s.code: s for s in db.scalars(select(Subject).where(Subject.organization_id == org_id))}
    for i, (code, name) in enumerate(SUBJECTS):
        if code not in subjects:
            subjects[code] = Subject(organization_id=org_id, code=code, name=name, sort=i)
            db.add(subjects[code])
    have_grades = set(db.scalars(select(Grade.level).where(Grade.organization_id == org_id)))
    for g in GRADES:
        if g not in have_grades:
            db.add(Grade(organization_id=org_id, level=g, name=f"Lớp {g}"))
    have_sem = set(db.scalars(select(Semester.code).where(Semester.organization_id == org_id)))
    for i, (code, name) in enumerate(SEMESTERS):
        if code not in have_sem:
            db.add(Semester(organization_id=org_id, code=code, name=name, sort=i))
    db.flush()

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
