import uuid

from pydantic import BaseModel

from app.schemas.documents import DocumentOut


class ReviewDocumentOut(BaseModel):
    document: DocumentOut
    total: int
    counts: dict[str, int]
    spot_pending: int
    progress: float
    assigned_to: uuid.UUID | None
    assigned_name: str | None


class AssignIn(BaseModel):
    assigned_to: uuid.UUID | None
