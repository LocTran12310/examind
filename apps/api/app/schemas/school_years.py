from datetime import date, datetime
import uuid

from pydantic import BaseModel, Field


class TermIO(BaseModel):
    code: str
    name: str | None = None
    start_date: date
    end_date: date


class YearIn(BaseModel):
    code: str = Field(min_length=9, max_length=9)
    name: str | None = Field(default=None, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    terms: list[TermIO] | None = None


class YearUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    terms: list[TermIO] | None = None


class YearOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    start_date: date
    end_date: date
    status: str
    terms: list[TermIO]
    class_count: int = 0


class AuditOut(BaseModel):
    id: uuid.UUID
    created_at: datetime
    organization_id: uuid.UUID
    organization_code: str | None
    actor_id: uuid.UUID | None
    actor_name: str | None
    action: str
    target_type: str
    target_id: uuid.UUID | None
    data: dict


def year_out(y, n=0) -> YearOut:
    return YearOut(id=y.id, code=y.code, name=y.name, start_date=y.start_date, end_date=y.end_date, status=y.status,
                   terms=[TermIO(code=t.code, name=t.name, start_date=t.start_date, end_date=t.end_date) for t in y.terms], class_count=n or 0)
