"""Triage parsed questions: search text, near-duplicates, auto-approve vs review, spot checks (US-01, A-02, A-03, A-07)."""
import random
import re

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import Question
from app.models.question import USABLE
from app.services.question_quality import evaluate, triage_status
from app.services.search_text import for_question

DUPLICATE_SIMILARITY = 0.9
SPOT_RATIO = 0.05


def find_duplicate(db: Session, q: Question) -> Question | None:
    if len(q.search_text) < 15:
        return None
    rows = db.execute(text("""
        select id, similarity(search_text, :t) as s from questions
         where organization_id = :o and status = any(:usable) and type = :type and id <> :id
           and (cast(:doc as uuid) is null or source_document_id is distinct from cast(:doc as uuid)) and search_text % :t
         order by s desc limit 5"""),
        {"t": q.search_text, "o": q.organization_id, "usable": list(USABLE), "type": q.type, "id": q.id, "doc": q.source_document_id}).all()
    digits = re.findall(r"\d+", q.search_text)
    for qid, sim in rows:
        if sim < DUPLICATE_SIMILARITY:
            break
        other = db.get(Question, qid)
        # same wording with different numbers is a different question
        if re.findall(r"\d+", other.search_text) == digits:
            return other
    return None


def triage_questions(db: Session, questions: list[Question], threshold: float, seed: str = "") -> dict:
    counts = {"auto_approved": 0, "needs_review": 0, "duplicate": 0, "spot_check": 0}
    auto: list[Question] = []
    for q in questions:
        q.search_text = for_question(q.stem, q.options)
    db.flush()
    for q in questions:
        dup = find_duplicate(db, q)
        if dup is not None:
            q.status, q.duplicate_of = "duplicate", dup.id
            counts["duplicate"] += 1
            continue
        q.status = triage_status(q.confidence, q.issues or [], threshold)
        counts[q.status] += 1
        if q.status == "auto_approved":
            auto.append(q)
    if auto:
        k = max(1, round(len(auto) * SPOT_RATIO))
        for q in random.Random(seed).sample(auto, k):
            q.spot_check = True
        counts["spot_check"] = k
    db.flush()
    return counts


def triage_hook(db, doc, rows, ctx) -> None:
    threshold = float((doc.processing_config or {}).get("threshold", 0.85))
    counts = triage_questions(db, [q for _, q in rows], threshold, seed=str(doc.id))
    ctx.step("triage", **counts)


def triage_legacy_drafts(db: Session) -> int:
    """Questions stored before the review workflow existed are still `draft`: triage them once."""
    drafts = db.scalars(select(Question).where(Question.status == "draft")).all()
    for q in drafts:
        q.issues, q.confidence = evaluate(q.type, q.stem, q.options or [], q.answer, q.solution,
                                          extra_issues=[i for i in q.issues or [] if i != "thiếu lời giải"], ocr=q.parse_method == "ocr")
    if drafts:
        triage_questions(db, drafts, 0.85, seed="legacy")
    return len(drafts)
