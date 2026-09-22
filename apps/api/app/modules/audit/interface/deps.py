"""Builds the audit handlers for a request."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.modules.audit.application.queries.search_audit import SearchAuditHandler
from app.modules.audit.infrastructure.read_models import SqlAuditReader
from app.shared.infrastructure.db import get_db


def search_audit(db: Session = Depends(get_db)) -> SearchAuditHandler:
    return SearchAuditHandler(SqlAuditReader(db))
