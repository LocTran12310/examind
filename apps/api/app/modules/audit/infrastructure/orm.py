"""Maps the audit entry onto audit_logs (architecture-refactor ADR-01); writes go through the shared AuditTrail."""
from app.modules.audit.domain.entities import AuditEntry
from app.shared.infrastructure.db import mapper_registry
from app.shared.infrastructure.schema.audit import audit_logs

if not any(m.class_ is AuditEntry for m in mapper_registry.mappers):
    mapper_registry.map_imperatively(AuditEntry, audit_logs)
