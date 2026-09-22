from fastapi import Depends
from sqlalchemy.orm import Session

from app.shared.infrastructure.db import get_db
from app.shared.infrastructure.sql_unit_of_work import SqlUnitOfWork


def unit_of_work(db: Session = Depends(get_db)) -> SqlUnitOfWork:
    return SqlUnitOfWork(db)
