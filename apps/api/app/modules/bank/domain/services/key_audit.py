"""Flag MCQs whose answer key contradicts what the best students chose (adaptive-review ADR-03, A-08, A-09)."""
from collections import Counter

from app.modules.bank.domain.entities import Question

FLAG = "Nghi sai đáp án"
MIN_ANSWERS = 10
TOP_SHARE = 0.6
LOW_CORRECT, LOW_CORRECT_MIN = 0.15, 20
RECHECK_AFTER = 10  # new answers needed before re-flagging a question a teacher confirmed


def evidence_for(rows: list[tuple[dict | None, float]], key: str) -> dict | None:
    """rows = (response, attempt score ratio). Returns evidence when the key looks wrong."""
    n = len(rows)
    if n < MIN_ANSWERS:
        return None
    counts = Counter((r or {}).get("key") or "—" for r, _ in rows)
    overall = counts.get(key, 0) / n
    ranked = sorted(rows, key=lambda x: -x[1])
    top = ranked[: max(3, n // 4)]
    top_counts = Counter((r or {}).get("key") or "—" for r, _ in top)
    choice, votes = top_counts.most_common(1)[0]
    share = votes / len(top)
    reason = None
    if choice != key and choice != "—" and share >= TOP_SHARE:
        reason = f"{round(share * 100)}% học sinh nhóm giỏi chọn {choice}, đáp án đang là {key}"
    elif n >= LOW_CORRECT_MIN and overall < LOW_CORRECT and top_counts.get(key, 0) / len(top) < 0.3:
        reason = f"Chỉ {round(overall * 100)}% trả lời đúng, kể cả nhóm giỏi"
    if not reason:
        return None
    return {"reason": reason, "answers": n, "key": key, "overall_correct": round(overall, 3),
            "top_quartile": {"size": len(top), "choice": choice, "share": round(share, 3)}, "option_counts": dict(counts)}


def audit_question(q: Question, rows: list[tuple[dict | None, float]]) -> dict | None:
    """Flag `q` when its answers contradict the key; returns the evidence (None = left alone)."""
    key = (q.answer or {}).get("key")
    if not key:
        return None
    prev = q.flag_evidence or {}
    if prev.get("dismissed") and len(rows) < prev.get("answers_at_dismiss", 0) + RECHECK_AFTER:
        return None
    ev = evidence_for(rows, key)
    if ev is None:
        return None
    q.status, q.spot_check, q.flag_evidence = "flagged", False, ev
    q.issues = list(dict.fromkeys([*(q.issues or []), FLAG]))
    return ev
