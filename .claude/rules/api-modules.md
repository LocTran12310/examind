---
globs: apps/api/app/modules/**, apps/api/app/shared/**
paths: apps/api/app/modules/**, apps/api/app/shared/**
---

# API module layers

- `interface → infrastructure → application → domain`; nothing points outward.
- `domain/`: dataclasses, pure rules, ports (Protocol). No sqlalchemy, fastapi, pydantic, boto3 or starlette,
  and nothing from `shared.application|infrastructure|interface`.
- `application/`: one handler class per file (`commands/<verb>_<noun>.py`, `queries/<name>.py`), ports injected in
  `__init__`, frozen dataclass input, DTO output. Commands end with `uow.commit()`. No framework, no SQL.
- `infrastructure/`: `orm.py` (imperative mapping onto `shared/infrastructure/schema/<area>.py`),
  `repositories.py` (aggregates), `read_models.py` (search, facets, reports), `adapters/` (other modules, external tools).
- `interface/`: Pydantic schemas, `deps.py` building handlers, a thin `router.py`. Never raise `HTTPException` —
  raise a domain error and let the shared handler map it.
- Another module is reachable only through its `application/api.py`, wired in `main.py` / `app/worker/handlers.py`.
- Every repository and read model filters by `actor.org_id`.
- After editing: `cd apps/api && uv run ruff check . && uv run lint-imports`.
