"""SQL adapters over other contexts' tables the review workflow reads or updates in the same transaction:
source documents (assignment), the org's ingestion threshold, submitted MCQ answers (key audit)."""
import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.bank.domain.entities import USABLE
from app.modules.bank.infrastructure.tables import attempt_answers, attempts, source_documents
from app.shared.infrastructure.schema.bank import questions
from app.shared.infrastructure.schema.identity import organizations

DEFAULT_THRESHOLD = 0.85
d = source_documents.c


class SqlReviewDocuments:
    def __init__(self, session: Session):
        self.session = session

    def exists(self, org_id: uuid.UUID, document_id: uuid.UUID) -> bool:
        return self.session.scalar(select(d.id).where(d.id == document_id, d.organization_id == org_id)) is not None

    def assign(self, org_id: uuid.UUID, document_id: uuid.UUID, user_id: uuid.UUID | None) -> None:
        self.session.flush()
        self.session.execute(update(source_documents).where(d.id == document_id, d.organization_id == org_id).values(assigned_to=user_id)
                             .execution_options(synchronize_session=False))
        self.session.expire_all()  # a loaded SourceDocument (old layout) must see the new reviewer


class SqlReviewSettings:
    """organizations.settings.ingestion.threshold (the ingestion settings' auto-approval threshold)."""

    def __init__(self, session: Session):
        self.session = session

    def _settings(self, org_id: uuid.UUID) -> dict:
        self.session.flush()
        return self.session.scalar(select(organizations.c.settings).where(organizations.c.id == org_id)) or {}

    def threshold(self, org_id: uuid.UUID) -> float:
        return float(self._settings(org_id).get("ingestion", {}).get("threshold", DEFAULT_THRESHOLD))

    def set_threshold(self, org_id: uuid.UUID, value: float) -> None:
        settings = dict(self._settings(org_id))
        settings["ingestion"] = {**settings.get("ingestion", {}), "threshold": value}
        self.session.execute(update(organizations).where(organizations.c.id == org_id).values(settings=settings)
                             .execution_options(synchronize_session=False))
        self.session.expire_all()  # a loaded Organization must see the new settings


class SqlAnswerStats:
    def __init__(self, session: Session):
        self.session = session

    def mcq_answers(self, org_id: uuid.UUID | None) -> dict[uuid.UUID, list[tuple[dict | None, float]]]:
        a, t, q = attempt_answers.c, attempts.c, questions.c
        stmt = (select(a.question_id, a.response, t.score, t.max_score).select_from(attempt_answers)
                .join(attempts, t.id == a.attempt_id).join(questions, q.id == a.question_id)
                .where(t.status == "submitted", q.type == "mcq", q.status.in_(USABLE), a.points.is_not(None)))
        if org_id:
            stmt = stmt.where(q.organization_id == org_id)
        out: dict = {}
        for qid, response, score, max_score in self.session.execute(stmt):
            out.setdefault(qid, []).append((response, (score or 0) / max_score if max_score else 0))
        return out
