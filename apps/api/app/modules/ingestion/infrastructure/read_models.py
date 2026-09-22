import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.modules.ingestion.domain.entities import AiModel, SourceDocument
from app.modules.ingestion.infrastructure import orm  # noqa: F401  (mapping)
from app.shared.application.search import Page, SearchRequest
from app.shared.infrastructure.sql_search import Col, search

D = SourceDocument
DOCUMENT_COLS = {
    "filename": Col(D.filename),
    "source_name": Col(D.meta["source_name"].astext),
    "status": Col(D.status, "exact"),
    "mime": Col(D.mime, "exact"),
    "question_count": Col(D.question_count, "number"),
    "created_at": Col(D.created_at, "date"),
}

MODEL_COLS = {
    "name": Col(AiModel.name),
    "provider": Col(AiModel.provider, "exact"),
    "model": Col(AiModel.model),
    "enabled": Col(AiModel.enabled, "bool"),
    "is_free": Col(AiModel.is_free, "bool"),
}


class SqlDocumentReader:
    def __init__(self, session: Session):
        self.session = session

    def search(self, org_id: uuid.UUID, req: SearchRequest) -> Page[SourceDocument]:
        stmt = select(D).where(D.organization_id == org_id)
        rows, total = search(self.session, stmt, req, DOCUMENT_COLS, text=[D.filename, D.meta["source_name"].astext],
                             default_sort=[D.created_at.desc(), D.id])
        return Page(list(rows), total, req.page, req.limit)


class SqlAiModelReader:
    def __init__(self, session: Session):
        self.session = session

    def search(self, org_id: uuid.UUID | None, req: SearchRequest) -> Page[AiModel]:
        stmt = select(AiModel)
        if org_id is not None:
            stmt = stmt.where(or_(AiModel.organization_id == org_id, AiModel.organization_id.is_(None)))
        else:
            stmt = stmt.where(AiModel.organization_id.is_(None))
        rows, total = search(self.session, stmt, req, MODEL_COLS, text=[AiModel.name, AiModel.model],
                             default_sort=[AiModel.organization_id.nulls_first(), AiModel.name, AiModel.id])
        return Page(list(rows), total, req.page, req.limit)
