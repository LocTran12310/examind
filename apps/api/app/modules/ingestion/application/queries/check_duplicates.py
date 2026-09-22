from dataclasses import dataclass

from app.modules.ingestion.application.dto import DuplicateReport, brief
from app.modules.ingestion.domain.ports import DocumentRepository
from app.modules.ingestion.domain.services.documents import norm_name
from app.shared.application.actor import Actor


@dataclass(frozen=True)
class CheckDuplicates:
    files: list[dict]  # {name, size?, sha256}


class CheckDuplicatesHandler:
    """Before uploading: which files are already here (same content) or share a name with a document."""

    def __init__(self, documents: DocumentRepository):
        self.documents = documents

    def __call__(self, actor: Actor, query: CheckDuplicates) -> list[DuplicateReport]:
        docs = self.documents.of_org(actor.org_id)
        by_hash = {d.file_hash: d for d in docs}
        by_name: dict[str, list] = {}
        for d in docs:
            by_name.setdefault(norm_name(d.filename), []).append(d)
        out = []
        for f in query.files:
            same = by_hash.get(str(f.get("sha256") or "").lower())
            names = [d for d in by_name.get(norm_name(f.get("name", "")), []) if d is not same]
            out.append(DuplicateReport(name=f.get("name"), same_file=brief(same) if same else None,
                                       same_name=[brief(d) for d in sorted(names, key=lambda d: d.created_at, reverse=True)]))
        return out
