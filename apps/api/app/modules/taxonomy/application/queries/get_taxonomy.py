from app.modules.taxonomy.application.dto import TaxonomyView
from app.modules.taxonomy.application.ports import TaxonomyReader
from app.shared.application.actor import Actor


class GetTaxonomyHandler:
    """Subjects, grades (with their cấp học) and semesters of the org."""

    def __init__(self, reader: TaxonomyReader):
        self.reader = reader

    def __call__(self, actor: Actor) -> TaxonomyView:
        return self.reader.get(actor.org_id)
