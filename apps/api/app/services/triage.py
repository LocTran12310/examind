"""Triage moved to the bank module (architecture-refactor UOW-04); the ingestion hook and the legacy-draft pass stay here."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Question
from app.modules.bank.domain.services.quality import evaluate
from app.modules.bank.interface.deps import bank_api


def triage_questions(db: Session, questions: list[Question], threshold: float, seed: str = "") -> dict:
    return vars(bank_api(db).triage(list(questions), threshold, seed))


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
