from sqlalchemy.orm import Session


class SqlUnitOfWork:
    """UnitOfWork over the request's SQLAlchemy session."""

    def __init__(self, session: Session):
        self.session = session

    def commit(self) -> None:
        self.session.commit()

    def flush(self) -> None:
        self.session.flush()

    def rollback(self) -> None:
        self.session.rollback()
