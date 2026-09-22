import uuid

from pydantic import BaseModel, Field

from app.shared.interface.search_schemas import SearchBody


class TagOut(BaseModel):
    id: uuid.UUID
    group: str
    name: str
    subject_id: uuid.UUID | None = None


class TagIn(BaseModel):
    group: str = "custom"
    name: str = Field(min_length=1, max_length=100)
    subject_id: uuid.UUID | None = None


class TagUpdate(BaseModel):
    group: str | None = None
    name: str | None = Field(default=None, max_length=100)
    subject_id: uuid.UUID | None = None  # sent as null = make it shared


class TagSearchBody(SearchBody):
    """`subject_id`: a subject's tags plus shared ones (pickers); "shared" = shared only;
    `include_shared=false` = exactly that subject (the Tags page filter)."""
    subject_id: str | None = None
    include_shared: bool = True
