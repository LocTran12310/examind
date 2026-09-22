"""Builds the taxonomy handlers for a request (composition of ports and adapters)."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.modules.taxonomy.application.commands.create_tag import CreateTagHandler
from app.modules.taxonomy.application.commands.create_topic import CreateTopicHandler
from app.modules.taxonomy.application.commands.delete_tag import DeleteTagHandler
from app.modules.taxonomy.application.commands.delete_topic import DeleteTopicHandler
from app.modules.taxonomy.application.commands.merge_topic import MergeTopicHandler
from app.modules.taxonomy.application.commands.move_topic import MoveTopicHandler
from app.modules.taxonomy.application.commands.update_tag import UpdateTagHandler
from app.modules.taxonomy.application.commands.update_topic import UpdateTopicHandler
from app.modules.taxonomy.application.queries.get_taxonomy import GetTaxonomyHandler
from app.modules.taxonomy.application.queries.list_topics import ListTopicsHandler
from app.modules.taxonomy.application.queries.search_tags import SearchTagsHandler
from app.modules.taxonomy.infrastructure.read_models import SqlTagReader, SqlTaxonomyReader, SqlTopicReader
from app.modules.taxonomy.infrastructure.repositories import SqlSubjectLookup, SqlTagRepository, SqlTopicReferences, SqlTopicRepository
from app.shared.infrastructure.db import get_db
from app.shared.infrastructure.sql_audit import SqlAuditTrail
from app.shared.infrastructure.sql_unit_of_work import SqlUnitOfWork


def create_tag(db: Session = Depends(get_db)) -> CreateTagHandler:
    return CreateTagHandler(SqlTagRepository(db), SqlSubjectLookup(db), SqlUnitOfWork(db))


def update_tag(db: Session = Depends(get_db)) -> UpdateTagHandler:
    return UpdateTagHandler(SqlTagRepository(db), SqlSubjectLookup(db), SqlUnitOfWork(db))


def delete_tag(db: Session = Depends(get_db)) -> DeleteTagHandler:
    return DeleteTagHandler(SqlTagRepository(db), SqlUnitOfWork(db))


def search_tags(db: Session = Depends(get_db)) -> SearchTagsHandler:
    return SearchTagsHandler(SqlTagReader(db))


def get_taxonomy(db: Session = Depends(get_db)) -> GetTaxonomyHandler:
    return GetTaxonomyHandler(SqlTaxonomyReader(db))


def list_topics(db: Session = Depends(get_db)) -> ListTopicsHandler:
    return ListTopicsHandler(SqlTopicReader(db))


def create_topic(db: Session = Depends(get_db)) -> CreateTopicHandler:
    return CreateTopicHandler(SqlTopicRepository(db), SqlSubjectLookup(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def update_topic(db: Session = Depends(get_db)) -> UpdateTopicHandler:
    return UpdateTopicHandler(SqlTopicRepository(db), SqlUnitOfWork(db))


def move_topic(db: Session = Depends(get_db)) -> MoveTopicHandler:
    return MoveTopicHandler(SqlTopicRepository(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def merge_topic(db: Session = Depends(get_db)) -> MergeTopicHandler:
    return MergeTopicHandler(SqlTopicRepository(db), SqlTopicReferences(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def delete_topic(db: Session = Depends(get_db)) -> DeleteTopicHandler:
    return DeleteTopicHandler(SqlTopicRepository(db), SqlTopicReferences(db), SqlAuditTrail(db), SqlUnitOfWork(db))
