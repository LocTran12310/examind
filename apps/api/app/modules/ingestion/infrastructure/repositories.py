import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.ingestion.domain.entities import AiModel, Asset, SourceDocument
from app.modules.ingestion.infrastructure import orm  # noqa: F401  (mapping)


class SqlDocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, org_id: uuid.UUID, document_id: uuid.UUID) -> SourceDocument | None:
        doc = self.session.get(SourceDocument, document_id)
        return doc if doc is not None and doc.organization_id == org_id else None

    def get_any(self, document_id: uuid.UUID) -> SourceDocument | None:
        return self.session.get(SourceDocument, document_id)

    def by_hash(self, org_id: uuid.UUID, file_hash: str) -> SourceDocument | None:
        return self.session.scalar(select(SourceDocument).where(SourceDocument.organization_id == org_id, SourceDocument.file_hash == file_hash))

    def of_org(self, org_id: uuid.UUID) -> list[SourceDocument]:
        return list(self.session.scalars(select(SourceDocument).where(SourceDocument.organization_id == org_id)))

    def add(self, doc: SourceDocument) -> None:
        self.session.add(doc)
        self.session.flush()

    def remove(self, doc: SourceDocument) -> None:
        self.session.delete(doc)


class SqlAssetRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, org_id: uuid.UUID, asset_id: uuid.UUID) -> Asset | None:
        a = self.session.get(Asset, asset_id)
        return a if a is not None and a.organization_id == org_id else None

    def add(self, asset: Asset) -> None:
        self.session.add(asset)
        self.session.flush()


class SqlAiModelRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, model_id: uuid.UUID) -> AiModel | None:
        return self.session.get(AiModel, model_id)

    def add(self, m: AiModel) -> None:
        self.session.add(m)
        self.session.flush()

    def remove(self, m: AiModel) -> None:
        self.session.delete(m)
