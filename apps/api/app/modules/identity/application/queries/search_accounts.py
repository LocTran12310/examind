from dataclasses import dataclass

from app.modules.identity.application.dto import AccountView
from app.modules.identity.application.ports import AccountReader
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchAccounts:
    request: SearchRequest


class SearchAccountsHandler:
    """Every account of every org (school-years AC-14)."""

    def __init__(self, reader: AccountReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: SearchAccounts) -> Page[AccountView]:
        return self.reader.search(query.request)
