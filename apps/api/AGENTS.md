# apps/api — working agreement

FastAPI + SQLAlchemy 2 (imperative mapping) + Alembic, Postgres (ltree, pgvector), MinIO, a job worker in the
same package. Python 3.12, dependencies with `uv`. Read [`.ai/architecture.md`](../../.ai/architecture.md) first;
the root [`AGENTS.md`](../../AGENTS.md) holds the rules shared with the web app.

## Layout

```
app/main.py            composition root: middleware, error handlers, actor resolver, cross-module adapters, routers
app/metadata.py        every Table + every ORM mapping (Alembic, seeds and tests import it)
app/shared/            shared kernel: domain errors & clock, search contract, unit of work, Actor, SQL search,
                       config, storage, logging, business calendar, request id, auth dependencies
app/modules/<context>/ identity · academic · taxonomy · bank · ingestion · assessment · analytics · audit
    domain/            dataclass entities, value objects, pure rules, ports (Protocol)
    application/       commands/<verb>_<noun>.py, queries/<name>.py (one handler class each), dto.py, api.py
    infrastructure/    orm.py, repositories.py, read_models.py, adapters/ (other modules, LibreOffice, OCR, LLM, S3)
    interface/         router.py, schemas.py (Pydantic), deps.py (builds handlers)
app/worker/            job loop; each job type calls an application command
app/seed/              system org, super admin, per-org reference data
migrations/versions/   Alembic revisions
tests/                 HTTP tests per resource, tests/unit/ handler tests on fake ports, architecture & drift tests
```

## Rules (all linted)

- Inside a module: `interface → infrastructure → application → domain`. Nothing points outward.
- `domain` imports no sqlalchemy / fastapi / pydantic / boto3 / starlette, and nothing from `shared.application`,
  `shared.infrastructure` or `shared.interface`. It holds rules, not I/O.
- `application` sees ports (Protocol) and dataclasses only — no framework, no adapter, no SQL.
- A module reaches another module only through its `application/api.py`; the adapter is wired in `main.py`
  (and `app/worker/handlers.py` for jobs). Never import another module's domain, infrastructure or interface.
- `shared` never imports `modules`, `main`, `metadata`, `worker` or `seed`.
- Tables live in `shared/infrastructure/schema/<area>.py` — one definition per physical table; the owning module
  maps its dataclasses onto them in `infrastructure/orm.py`.
- Repositories and read models filter by `actor.org_id`. A handler never trusts an organisation id from the request.
- Errors are domain errors (`NotFound`, `Conflict`, `Invalid`, `Forbidden`, `Unauthenticated`, `Throttled`,
  `Misconfigured`); the interface layer maps them to HTTP. Never raise `HTTPException`.
- Commands commit through `UnitOfWork`; queries do not write.

## Checks

```bash
cd apps/api
uv run ruff check .            # style; `uv run ruff check --fix .` for the mechanical part
uv run lint-imports            # the layer contracts (.importlinter)
cd ../.. && ./scripts/verify.sh apps/api/tests                       # full suite in the api-test image
./scripts/verify.sh apps/api/tests/unit                              # handler tests only (fast, no database)
EXAMIN_DIR=<papers dir> ./scripts/verify.sh apps/api/tests/test_golden_official.py
```

`tests/test_architecture.py` enforces the rules above, `tests/test_schema_drift.py` runs `alembic check`.
The API suite needs the compose Postgres and MinIO; `scripts/verify.sh` starts them.

## Adding an endpoint (short form — the `api-endpoint` skill has the long one)

1. Rule or state change → `domain/` (entity method or pure service), with a port if it needs data.
2. Use case → `application/commands|queries/<name>.py`: a frozen dataclass for the input, a handler class taking
   ports in `__init__`, returning a DTO. Commands call `uow.commit()`.
3. Persistence → `infrastructure/repositories.py` (aggregates) or `read_models.py` (search, facets, reports).
4. HTTP → `interface/schemas.py` (Pydantic), `interface/deps.py` (build the handler), `interface/router.py` (thin).
5. Tests → a handler test in `tests/unit/` with fake ports, plus an HTTP test in `tests/test_<area>_api.py`.
