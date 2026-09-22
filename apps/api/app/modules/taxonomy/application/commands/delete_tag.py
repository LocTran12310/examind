from dataclasses import dataclass
import uuid

from app.modules.taxonomy.application.commands._tags import load_tag
from app.modules.taxonomy.domain.ports import TagRepository
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class DeleteTag:
    tag_id: uuid.UUID


class DeleteTagHandler:
    def __init__(self, tags: TagRepository, uow: UnitOfWork):
        self.tags, self.uow = tags, uow

    def __call__(self, actor: Actor, cmd: DeleteTag) -> None:
        self.tags.remove(load_tag(self.tags, actor.org_id, cmd.tag_id))
        self.uow.commit()
