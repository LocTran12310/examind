"""Per-topic mastery as a difficulty-weighted moving average (adaptive-review ADR-01, A-01, A-02)."""
from datetime import datetime
import uuid

from app.modules.analytics.domain.entities import TopicMastery
from app.modules.analytics.domain.value_objects import TopicNode

ALPHA = 0.3
START = 0.5
WEIGHT = {"nb": 0.8, "th": 1.0, "vd": 1.2, "vdc": 1.4}


def step(current: float, ratio: float, difficulty: str | None) -> float:
    a = min(1.0, ALPHA * WEIGHT.get(difficulty or "th", 1.0))
    return round(current + a * (ratio - current), 6)


def fresh(student_id: uuid.UUID, topic_id: uuid.UUID, org_id: uuid.UUID) -> TopicMastery:
    return TopicMastery(student_id=student_id, topic_id=topic_id, organization_id=org_id, mastery=START, answers=0)


def apply(row: TopicMastery, ratio: float, difficulty: str | None, at: datetime | None) -> None:
    """One more graded answer on the topic."""
    row.mastery = step(row.mastery, ratio, difficulty)
    row.answers = (row.answers or 0) + 1
    row.last_at = at


def rollup(leaves: list[tuple[TopicMastery, TopicNode]], topics: dict[uuid.UUID, TopicNode]) -> list[dict]:
    """Leaf rows plus parents rolled up (answers-weighted), sorted by path."""
    if not leaves:
        return []
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


def weakest(rows: list[dict], n: int = 3) -> list[dict]:
    tracked = [r for r in rows if r["tracked"] and r["mastery"] is not None]
    return sorted(tracked, key=lambda r: r["mastery"])[:n]
