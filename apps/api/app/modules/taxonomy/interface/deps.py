"""Builds the taxonomy handlers for a request (composition of ports and adapters)."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.modules.taxonomy.application.commands.create_tag import CreateTagHandler
from app.modules.taxonomy.application.commands.delete_tag import DeleteTagHandler
from app.modules.taxonomy.application.commands.update_tag import UpdateTagHandler
from app.modules.taxonomy.application.queries.search_tags import SearchTagsHandler
from app.modules.taxonomy.infrastructure.read_models import SqlTagReader
from app.modules.taxonomy.infrastructure.repositories import SqlSubjectLookup, SqlTagRepository
from app.shared.infrastructure.db import get_db
from app.shared.infrastructure.sql_unit_of_work import SqlUnitOfWork


def create_tag(db: Session = Depends(get_db)) -> CreateTagHandler:
    return CreateTagHandler(SqlTagRepository(db), SqlSubjectLookup(db), SqlUnitOfWork(db))


def update_tag(db: Session = Depends(get_db)) -> UpdateTagHandler:
    return UpdateTagHandler(SqlTagRepository(db), SqlSubjectLookup(db), SqlUnitOfWork(db))


def delete_tag(db: Session = Depends(get_db)) -> DeleteTagHandler:
    return DeleteTagHandler(SqlTagRepository(db), SqlUnitOfWork(db))


def search_tags(db: Session = Depends(get_db)) -> SearchTagsHandler:
    return SearchTagsHandler(SqlTagReader(db))
