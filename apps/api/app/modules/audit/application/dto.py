from dataclasses import dataclass

from app.modules.audit.domain.entities import AuditEntry


@dataclass(frozen=True)
class AuditRow:
    entry: AuditEntry
    actor_name: str | None
    organization_code: str | None
