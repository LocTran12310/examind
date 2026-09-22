---
globs: apps/api/migrations/**, apps/api/app/shared/infrastructure/schema/**
paths: apps/api/migrations/**, apps/api/app/shared/infrastructure/schema/**
---

# Schema changes

- The physical schema is `app/shared/infrastructure/schema/<area>.py`; `app/metadata.py` loads every table and
  mapping. Declare indexes and constraints there, not only in the migration.
- One change = one Alembic revision: `make revision m="what changed"`, then read the generated file — autogenerate
  misses server defaults, index names on expressions and data moves.
- A migration that changes data must be reversible or state plainly in its docstring that it is not.
- `tests/test_schema_drift.py` runs `alembic check`: metadata and migrations must agree.
- Never edit an applied revision; add a new one. Never point Alembic at a production database by hand.
