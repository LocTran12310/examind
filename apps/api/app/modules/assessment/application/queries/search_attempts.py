from dataclasses import dataclass, replace

from app.modules.assessment.application.dto import AttemptRow
from app.modules.assessment.application.ports import AttemptHistoryReader
from app.shared.application.actor import Actor
from app.shared.application.search import Filter, Page, SearchRequest


@dataclass(frozen=True)
class SearchAttempts:
    request: SearchRequest


class SearchAttemptsHandler:
    """What a student has sat: which paper, when it started, when it was handed in, how long that took (AC-01).

    **Scope comes from the caller, never from the body.** A student's request is rewritten to their own id
    whatever `student_id` it carried; staff see their organisation. F20 is the reason this is spelled out: a page
    called "của tôi" answered with the whole organisation's numbers because the read model widened by default
    and nobody re-read it after the roles changed.
    """

    def __init__(self, reader: AttemptHistoryReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: SearchAttempts) -> Page[AttemptRow]:
        request = query.request
        if not actor.is_staff:
            request = replace(request, filters={**request.filters, "student_id": Filter(value=str(actor.user_id))})
        return self.reader.search(actor.org_id, request)
