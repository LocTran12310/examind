"""Question presenter shared by the exam and attempt routers (old layout), through the bank module."""
from sqlalchemy.orm import Session

from app.modules.bank.interface.schemas import ParsedQuestionOut, parsed_out


def parsed_many(db: Session, qs: list, groups: dict | None = None) -> list[ParsedQuestionOut]:
    """Questions with topics and tags, through the bank module (its presenter)."""
    from app.modules.bank.interface.deps import bank_api

    return [parsed_out(v) for v in bank_api(db).views(list(qs), groups)]
