from dataclasses import dataclass
import uuid

from app.modules.taxonomy.application.commands._tags import ensure_subject, ensure_unique, load_tag
from app.modules.taxonomy.application.dto import TagView, tag_view
from app.modules.taxonomy.domain.ports import SubjectLookup, TagRepository
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork

UNCHANGED = object()


@dataclass(frozen=True)
class UpdateTag:
    tag_id: uuid.UUID
    group: str | None = None
    name: str | None = None
    subject_id: object = UNCHANGED  # None = make it shared


class UpdateTagHandler:
    def __init__(self, tags: TagRepository, subjects: SubjectLookup, uow: UnitOfWork):
        self.tags, self.subjects, self.uow = tags, subjects, uow

    def __call__(self, actor: Actor, cmd: UpdateTag) -> TagView:
        tag = load_tag(self.tags, actor.org_id, cmd.tag_id)
        tag.change(cmd.group, cmd.name)
        if cmd.subject_id is not UNCHANGED:
            ensure_subject(self.subjects, actor.org_id, cmd.subject_id)
            tag.assign_subject(cmd.subject_id)
        ensure_unique(self.tags, tag)
        self.uow.commit()
        return tag_view(tag)
