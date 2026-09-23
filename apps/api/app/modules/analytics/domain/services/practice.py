"""Rules of a personal review exam (adaptive-review US-02, US-03, A-03..A-07, ADR-02): which share of the questions
targets weak topics, re-asks old mistakes or fills in, at which difficulty, and how the plan is summarised."""
from datetime import datetime, timedelta
import random
import uuid

from app.modules.analytics.domain.value_objects import Plan
from app.shared.domain.errors import Invalid

WEAK_SHARE, REASK_SHARE = 0.6, 0.1
PLAN_TOPICS = 3  # how many topics a plan targets; which ones are weak is mastery.weak_topics()
CONSOLIDATE_BELOW = 0.8  # mastery a topic is still worth consolidating below
RECENT_CORRECT_DAYS = 7
REASK_AFTER = timedelta(hours=24)
PRACTICE_MINUTES = 60
MIN_COUNT, MAX_COUNT = 5, 50


def target_difficulties(m: float | None) -> list[str]:
    if m is None or m < 0.4:
        return ["nb", "th"]
    if m < 0.7:
        return ["th", "vd"]
    return ["vd", "vdc"]


def draw(rng: random.Random, pool: list[tuple], n: int, preferred: list[str]) -> list[uuid.UUID]:
    """Prefer the target difficulties (unknown difficulty counts as 'th'), then fall back to anything."""
    pref = [qid for qid, d in pool if (d or "th") in preferred]
    rest = [qid for qid, d in pool if (d or "th") not in preferred]
    rng.shuffle(pref)
    rng.shuffle(rest)
    return (pref + rest)[:n]


def shares(n: int, groups: int) -> list[int]:
    """`n` questions spread over `groups` topics, the first ones taking the remainder."""
    return [n // groups + (1 if i < n % groups else 0) for i in range(groups)]


def clamp_count(count: int) -> int:
    return max(MIN_COUNT, min(MAX_COUNT, int(count)))


def check_window(open_at: datetime, close_at: datetime, duration_minutes: int) -> None:
    if close_at <= open_at:
        raise Invalid("Thời gian đóng phải sau thời gian mở", "close_at")
    if not 1 <= duration_minutes <= 600:
        raise Invalid("Thời lượng từ 1 đến 600 phút", "duration_minutes")


def adaptive_settings(student_id: uuid.UUID, plan: Plan) -> dict:
    """What the exam keeps of the plan (its settings' `adaptive` block)."""
    return {"student_id": str(student_id), "note": plan.note,
            "plan": [{"question_id": str(p.question_id), "reason": p.reason, "topic": p.topic} for p in plan.picks]}


def plan_summary(settings: dict) -> dict:
    """{note, groups: [{reason, topic, count}]} from an exam's settings."""
    ad = (settings or {}).get("adaptive") or {}
    counts: dict = {}
    for p in ad.get("plan", []):
        key = (p["reason"], p.get("topic"))
        counts[key] = counts.get(key, 0) + 1
    return {"note": ad.get("note"), "groups": [{"reason": r, "topic": t, "count": n} for (r, t), n in counts.items()]}
