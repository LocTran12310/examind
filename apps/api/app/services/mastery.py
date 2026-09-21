"""Per-topic mastery as a difficulty-weighted moving average (adaptive-review ADR-01, A-01, A-02).

Run `python -m app.services.mastery backfill` to rebuild from answer_facts.
"""
import sys
import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import AnswerFact, StudentTopicMastery, Topic

ALPHA = 0.3
START = 0.5
WEIGHT = {"nb": 0.8, "th": 1.0, "vd": 1.2, "vdc": 1.4}


def step(current: float, ratio: float, difficulty: str | None) -> float:
    a = min(1.0, ALPHA * WEIGHT.get(difficulty or "th", 1.0))
    return round(current + a * (ratio - current), 6)


def apply_fact(db: Session, fact: AnswerFact) -> None:
    if not fact.topic_path:
        return
    topic_id = db.scalar(select(Topic.id).where(Topic.organization_id == fact.organization_id, Topic.path == fact.topic_path))
    if topic_id is None:
        return
    row = db.get(StudentTopicMastery, (fact.student_id, topic_id))
    if row is None:
        row = StudentTopicMastery(student_id=fact.student_id, topic_id=topic_id, organization_id=fact.organization_id, mastery=START, answers=0)
        db.add(row)
    row.mastery = step(row.mastery, fact.correct_ratio, fact.difficulty)
    row.answers = (row.answers or 0) + 1
    row.last_at = fact.created_at
    db.flush()


def backfill(db: Session, org_id=None) -> int:
    stmt = delete(StudentTopicMastery)
    facts = select(AnswerFact).order_by(AnswerFact.created_at, AnswerFact.id)
    if org_id:
        stmt = stmt.where(StudentTopicMastery.organization_id == org_id)
        facts = facts.where(AnswerFact.organization_id == org_id)
    db.execute(stmt)
    n = 0
    for fact in db.scalars(facts):
        apply_fact(db, fact)
        n += 1
    return n


def rows_for(db: Session, org_id, student_id) -> list[dict]:
    """Leaf rows plus parents rolled up (answers-weighted), sorted by path."""
    leaves = db.execute(select(StudentTopicMastery, Topic).join(Topic, Topic.id == StudentTopicMastery.topic_id)
                        .where(StudentTopicMastery.organization_id == org_id, StudentTopicMastery.student_id == student_id)).all()
    if not leaves:
        return []
    topics = {t.id: t for t in db.scalars(select(Topic).where(Topic.organization_id == org_id))}
    agg: dict = {}
    for m, t in leaves:
        cur = t
        while cur is not None:
            a = agg.setdefault(cur.id, {"w": 0.0, "n": 0, "leaf": False})
            a["w"] += m.mastery * m.answers
            a["n"] += m.answers
            if cur.id == t.id:
                a["leaf"] = True
            cur = topics.get(cur.parent_id)
    out = []
    for tid, a in agg.items():
        t = topics[tid]
        out.append({"topic_id": tid, "parent_id": t.parent_id, "name": t.name, "path": t.path, "depth": t.path.count(".") + 1,
                    "mastery": round(a["w"] / a["n"], 4) if a["n"] else None, "answers": a["n"], "tracked": a["leaf"]})
    return sorted(out, key=lambda r: r["path"])


if __name__ == "__main__":
    from app.core import db as dbmod

    if sys.argv[1:] == ["backfill"]:
        with dbmod.session_factory()() as s:
            print("facts replayed:", backfill(s))
            s.commit()
    else:
        print("usage: python -m app.services.mastery backfill")
