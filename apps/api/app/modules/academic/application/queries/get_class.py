from dataclasses import dataclass
import uuid

from app.modules.academic.application.common import load_class
from app.modules.academic.application.dto import ClassDetailView, class_view
from app.modules.academic.application.ports import ClassReader
from app.modules.academic.domain.ports import ClassRepository
from app.shared.application.actor import Actor


@dataclass(frozen=True)
class GetClass:
    class_id: uuid.UUID


class GetClassHandler:
    def __init__(self, classes: ClassRepository, reader: ClassReader):
        self.classes, self.reader = classes, reader

    def __call__(self, actor: Actor, query: GetClass) -> ClassDetailView:
        c = load_class(self.classes, actor.org_id, query.class_id)
        members = self.reader.members(c.id)
        return ClassDetailView(class_view(c, len(members)), members)
