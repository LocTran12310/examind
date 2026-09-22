from dataclasses import dataclass
import uuid

from app.modules.taxonomy.application.commands._tags import ensure_subject, ensure_unique
from app.modules.taxonomy.application.dto import TagView, tag_view
from app.modules.taxonomy.domain.entities import Tag
from app.modules.taxonomy.domain.ports import SubjectLookup, TagRepository
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class CreateTag:
    group: str
    name: str
    subject_id: uuid.UUID | None = None


class CreateTagHandler:
    def __init__(self, tags: TagRepository, subjects: SubjectLookup, uow: UnitOfWork):
        self.tags, self.subjects, self.uow = tags, subjects, uow

    def __call__(self, actor: Actor, cmd: CreateTag) -> TagView:
        tag = Tag.create(actor.org_id, cmd.group, cmd.name, cmd.subject_id)
        ensure_subject(self.subjects, actor.org_id, tag.subject_id)
        ensure_unique(self.tags, tag)
        self.tags.add(tag)
        self.uow.commit()
        return tag_view(tag)
