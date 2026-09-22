---
name: db-change
description: Change the database schema — table, column, index or data move — with the Alembic revision and the drift check.
---

# Change the schema

The metadata and the migrations must agree; `tests/test_schema_drift.py` runs `alembic check` and fails otherwise.

## Steps

1. **Declare the change** in `app/shared/infrastructure/schema/<area>.py` (the one definition of each physical
   table). Indexes and constraints belong here too, with the names the migration will create.
2. **Map it** in the owning module's `infrastructure/orm.py` if a new column belongs to a dataclass entity.
   `app/metadata.py` must import the table and the mapping.
3. **Generate the revision**: `make revision m="add answer_facts.topic_id"`, then read the file. Autogenerate
   misses: server defaults, expression indexes, renames (it writes drop + add), data moves, enum changes.
   Fix it by hand and keep `down_revision` right.
4. **Data moves** go in the same revision as the schema change and are written with plain `op.execute` SQL.
   State in the docstring what is not reversible.
5. **Apply and check**: `make migrate && ./scripts/verify.sh apps/api/tests/test_schema_drift.py`.
6. **Tests**: the behaviour that needs the column, not the column itself.

## Never

- Edit a revision that has been applied anywhere — add a new one.
- Point Alembic at production by hand; the api container runs `alembic upgrade head` on start.
- Drop or truncate live data to make a migration simpler. Back up first (`pg_dump` into `backups/`) and ask.
