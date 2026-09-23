"""Per-topic mastery as a difficulty-weighted moving average (adaptive-review ADR-01, A-01, A-02), the one rule that
says which topics are weak and the decay that pulls an untouched topic back toward the start (learning-telemetry
ADR-04, A-03, A-04)."""
from datetime import datetime, timedelta
import uuid

from app.modules.analytics.domain.entities import TopicMastery
from app.modules.analytics.domain.value_objects import TopicNode
from app.shared.domain.errors import Forbidden

ALPHA = 0.3
START = 0.5
WEIGHT = {"nb": 0.8, "th": 1.0, "vd": 1.2, "vdc": 1.4}
HALF_LIFE = timedelta(days=60)  # idle time after which half the distance to START is gone
WEAK_BELOW = 0.6  # the one weak-topic threshold (A-03)
MIN_ANSWERS = 5  # below this a topic is "chưa đủ dữ liệu", never weak
ADMIN = "org_admin"


def decay(current: float, last_at: datetime | None, at: datetime | None) -> float:
    """Mastery drifts back toward START while the topic is left alone: half the distance every HALF_LIFE (A-04).
    Computed from `last_at` whenever the value is read or updated, never written by a job."""
    if last_at is None or at is None:
        return current
    idle = (at - last_at).total_seconds()
    if idle <= 0:
        return current
    return round(START + (current - START) * 0.5 ** (idle / HALF_LIFE.total_seconds()), 6)


def step(current: float, ratio: float, difficulty: str | None, last_at: datetime | None = None,
         at: datetime | None = None) -> float:
    """One more answer on the topic, on top of what the idle time since `last_at` has already decayed."""
    a = min(1.0, ALPHA * WEIGHT.get(difficulty or "th", 1.0))
    current = decay(current, last_at, at)
    return round(current + a * (ratio - current), 6)


def fresh(student_id: uuid.UUID, topic_id: uuid.UUID, org_id: uuid.UUID) -> TopicMastery:
    return TopicMastery(student_id=student_id, topic_id=topic_id, organization_id=org_id, mastery=START, answers=0)


def apply(row: TopicMastery, ratio: float, difficulty: str | None, at: datetime | None) -> None:
    """One more graded answer on the topic."""
    row.mastery = step(row.mastery, ratio, difficulty, row.last_at, at)
    row.answers = (row.answers or 0) + 1
    row.last_at = at


def enough(answers: int | None) -> bool:
    """Enough answers on a topic to say anything about it; below this it is "chưa đủ dữ liệu" (A-03)."""
    return (answers or 0) >= MIN_ANSWERS


def is_weak(mastery: float | None, answers: int | None) -> bool:
    """The one weak-topic rule (ADR-04): below the threshold, with enough answers behind it."""
    return mastery is not None and enough(answers) and mastery < WEAK_BELOW


def _level(row: dict) -> tuple[float | None, int]:
    """(mastery, answers) of a rolled-up row; a parent is a sum, never a topic to plan around."""
    return (row["mastery"] if row["tracked"] else None), row["answers"]


def weak_topics(rows: list, n: int | None = None, level=_level) -> list:
    """The weak topics among `rows`, weakest first, at most `n` — the only definition the planner, the API and the
    UI use. `rows` are `rollup()`'s dicts unless `level` reads another shape; a topic with too few answers is
    reported as "chưa đủ dữ liệu" instead and never planned around."""
    weak = [r for r in rows if is_weak(*level(r))]
    weak.sort(key=lambda r: level(r)[0])
    return weak[:n] if n is not None else weak


def rollup(leaves: list[tuple[TopicMastery, TopicNode]], topics: dict[uuid.UUID, TopicNode], at: datetime | None = None) -> list[dict]:
    """Leaf rows plus parents rolled up (answers-weighted), sorted by path; every mastery decayed to `at` first."""
    if not leaves:
        return []
    agg: dict = {}
    for m, t in leaves:
        value = decay(m.mastery, m.last_at, at)
        cur = t
        while cur is not None:
            a = agg.setdefault(cur.id, {"w": 0.0, "n": 0, "leaf": False})
            a["w"] += value * m.answers
            a["n"] += m.answers
            if cur.id == t.id:
                a["leaf"] = True
            cur = topics.get(cur.parent_id)
    out = []
    for tid, a in agg.items():
        t = topics[tid]
        row = {"topic_id": tid, "parent_id": t.parent_id, "name": t.name, "path": t.path, "depth": t.path.count(".") + 1,
               "mastery": round(a["w"] / a["n"], 4) if a["n"] else None, "answers": a["n"], "tracked": a["leaf"]}
        out.append({**row, "enough_data": enough(row["answers"]), "weak": is_weak(*_level(row))})
    return sorted(out, key=lambda r: r["path"])


class Accumulator:
    """Mastery rebuilt in memory while the answer facts are replayed (the weekly backfill), by the same rules as
    live grading."""

    def __init__(self):
        self.rows: dict[tuple[uuid.UUID, uuid.UUID], TopicMastery] = {}

    def add(self, student_id: uuid.UUID, topic_id: uuid.UUID, org_id: uuid.UUID, ratio: float, difficulty: str | None,
            at: datetime | None) -> None:
        row = self.rows.get((student_id, topic_id))
        if row is None:
            row = self.rows[(student_id, topic_id)] = fresh(student_id, topic_id, org_id)
        apply(row, ratio, difficulty, at)


def check_rebuilder(role: str) -> None:
    """Only an organisation's admin replays its answer facts (A-07)."""
    if role != ADMIN:
        raise Forbidden()
