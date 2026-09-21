from sqlalchemy import func, select, text

from app.models.taxonomy import Grade, Semester, Subject, Topic
from app.seed.math_topics import MATH_TREE
from app.seed.org_template import seed_org
from tests.factories import make_org


def _count(nodes):
    return sum(1 + _count(c) for *_, c in nodes)


def test_seed_org_creates_tree_with_paths(db):
    org = make_org(db)
    seed_org(db, org.id)
    db.commit()
    topics = db.scalars(select(Topic).where(Topic.organization_id == org.id)).all()
    assert len(topics) == _count(MATH_TREE)
    by_id = {t.id: t for t in topics}
    for t in topics:
        parent = by_id.get(t.parent_id)
        assert (t.path.rsplit(".", 1)[0] == parent.path) if parent else ("." not in t.path)
    giai_tich = next(t for t in topics if t.name == "Giải tích")
    subtree = db.execute(
        text("select count(*) from topics where organization_id=:o and path <@ cast(:p as ltree)"),
        {"o": org.id, "p": giai_tich.path},
    ).scalar()
    assert subtree == 1 + _count(next(c for n, _, _, c in MATH_TREE if n == "Giải tích"))
    assert db.scalar(select(func.count()).select_from(Grade).where(Grade.organization_id == org.id)) == 7
    assert db.scalar(select(func.count()).select_from(Semester).where(Semester.organization_id == org.id)) == 2


def test_seed_org_is_idempotent(db):
    org = make_org(db)
    seed_org(db, org.id)
    seed_org(db, org.id)
    db.commit()
    assert db.scalar(select(func.count()).select_from(Topic).where(Topic.organization_id == org.id)) == _count(MATH_TREE)
    assert db.scalar(select(func.count()).select_from(Subject).where(Subject.organization_id == org.id)) == 6
