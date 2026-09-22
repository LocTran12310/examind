from dataclasses import dataclass
import uuid

from app.modules.identity.application.dto import UserView
from app.modules.identity.application.ports import UserReader
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchUsers:
    request: SearchRequest
    class_id: uuid.UUID | None = None  # members of one class (class detail)


class SearchUsersHandler:
    """Members of the actor's org; teachers see students only (A-05)."""

    def __init__(self, reader: UserReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: SearchUsers) -> Page[UserView]:
        return self.reader.search(actor.org_id, query.request, query.class_id, students_only=actor.role == "teacher")
