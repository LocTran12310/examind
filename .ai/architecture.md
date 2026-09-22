---
generated: 2026-09-22
repo_root: examind
generator: hand-written from the repo (architecture-refactor F13)
verified_by: Loc Tran (blanket pre-approval in chat, 2026-09-22 — confirm at final review)
---

# Architecture map — Examind

Monorepo: `apps/api` (FastAPI, SQLAlchemy 2, Alembic, Postgres + ltree/pgvector, MinIO), the worker (same
package), and `apps/web` (Next.js App Router, React 19, shadcn/ui, TanStack Query + Table, zustand).
Compose runs postgres, minio, api, worker, web and caddy (:8088).

While F13 runs, screens and modules move one bounded context at a time; code that has not moved yet
lives in the old layout (`app/routers|services|models|schemas`, web `components/<area>`, `lib/hooks.ts`).
New code goes only into the layout below.

## Backend (`apps/api/app`)

```
main.py                         composition root: error handlers, request id, actor resolver, routers
shared/                         shared kernel — no business rules
  domain/                       errors.py (DomainError, NotFound, Conflict, Invalid, Forbidden, Unauthenticated), clock.py, ids.py
  application/                  search.py (SearchRequest, Filter, SortKey, Page), unit_of_work.py (port), actor.py (Actor)
  infrastructure/               db.py (engine, session, mapper_registry, metadata), schema/<area>.py (Table objects),
                                sql_search.py (filters/sort/paging → SQL), sql_unit_of_work.py
  interface/                    errors.py, request_id.py, auth.py (current_actor, staff_actor), deps.py, search_schemas.py
modules/<context>/              identity · academic · taxonomy · bank · ingestion · assessment · analytics · audit
  domain/                       entities.py (dataclasses), value_objects.py, errors.py, ports.py (Protocol), services/ (pure rules)
  application/                  commands/<verb>_<noun>.py, queries/<name>.py — one handler class each, ports in __init__;
                                dto.py (frozen dataclasses), ports.py (read ports), api.py (what other modules may call)
  infrastructure/               orm.py (map_imperatively onto shared tables), repositories.py (Sql*Repository),
                                read_models.py (Sql*Reader: search/facets/reports), adapters/ (LibreOffice, LLM, OCR, S3…)
  interface/                    router.py (thin), schemas.py (Pydantic in/out), deps.py (builds handlers from adapters)
worker/                         job loop; each job type calls an application command
seed/                           system org, super admin, reference data
```

### Rules (linted: `.importlinter`, `tests/test_architecture.py`)
- Inside a module: `interface → infrastructure → application → domain`; nothing points outward.
- `domain` imports no sqlalchemy / fastapi / pydantic / boto3 / starlette and nothing from `shared.application|infrastructure|interface`.
- `application` imports no framework or adapter; it sees ports (Protocol) and dataclasses only.
- A module imports another module's `application` only (usually `application/api.py`), never its domain,
  infrastructure or interface.
- `shared` never imports `modules`.

### How a request flows
`router` (Pydantic body → command/query dataclass) → `Depends(deps.<handler>)` builds the handler with
`Sql*Repository(db)`, `Sql*Reader(db)`, `SqlUnitOfWork(db)` → handler applies the rules and calls
`uow.commit()` → router maps the returned DTO to the response schema.
The caller is an `Actor` (`current_actor` / `staff_actor`); every repository and reader filters by `actor.org_id`.

### Contracts
- Lists: `POST /api/<resource>/search`, body `{page, limit, q?, sort?: [{field, desc}], filters?: {<field>: {operator?, value?, from?, to?}}, …resource params}`
  → `{data, total, page, limit}`. Filter reading by column kind: text `* = + - !`; number/date/day `= < <= > >=`
  or `from`/`to`; enum/uuid/bool `value` (list = any of). Unknown field/operator → 422 `bad_filter`, bad sort → `bad_sort`.
- Errors: `{code, message, details: {fields?, requestId}}` + `X-Request-Id` header.
- Days are business days (Asia/Ho_Chi_Minh); timestamps stored and sent in UTC.
- JSON stays snake_case; sessions are httpOnly cookies (15 min access JWT, 30 day refresh).

### Tests (`apps/api/tests`)
- HTTP tests per resource (`test_<area>_api.py`) against a real Postgres (`scripts/verify.sh`).
- `tests/unit/` — handlers against in-memory fake ports, no database.
- `test_architecture.py` — dependency rules.

## Frontend (`apps/web/src`)

```
app/                                   routes only: page.tsx renders a page component; (app)/layout.tsx checks the session (getMe)
components/ui/                         shadcn CLI output, never edited
components/common/                     shared composites: DataTable/ (DataTable, DataTableView, FilterCell, Pagination, Toolbar), …
components/layout/                     Providers, shell, sidebar, switchers
components/page-components/<Page>/<Component>/<Component>.tsx
hooks/common/                          use-table-query (table state in the URL), …
hooks/react-query/use-query-<domain>.ts   useXxxQuery / useXxxSearchQuery / useXxxMutation — call services only
hooks/page-hooks/<page>/use-<page>-*.ts(x)  state and logic of one page (columns, dialogs, submit)
services/<module>.service.ts           `export const xService = {…}` — the only callers of lib/common/http
stores/common/, stores/page-stores/<page>/   zustand, UI state only (never server data)
constants/                             *.constant.ts; react-query-key.constant.ts holds <ENTITY>_KEYS
dtos/ (*.dto.ts request bodies) · interfaces/ (*.interface.ts entities, pages) · types/ (*.type.ts unions)
lib/common/                            http.ts, query-client.ts, search-body.ts, form-errors.ts, datetime.ts, list-memory.ts
lib/page-libs/<page>/                  pure helpers of one page
```

### Rules (ESLint `no-restricted-imports`)
- Only `services/**` import `http` from `lib/common/http` (components may use the `ApiError` class).
- Only `hooks/react-query/**` (plus `lib/common/query-client`, `components/layout/Providers`, tests) import `@tanstack/react-query`.
- `app/**` imports neither services nor query hooks.
- `components/common/**` never imports a page component.
- shadcn components are imported one file each; no native `<select>` or date inputs (OptionSelect, DatePicker).
- Named exports only, no barrel files; hooks `use-*.ts` (kebab-case), component folders PascalCase.

### Data flow
URL (filters, sort, page) → `useTableQuery` → `toSearchBody` → `useXxxSearchQuery(body)` →
`xService.search(body)` → `POST /api/x/search`. React Query owns server state: one QueryClient
(staleTime 0, retry 1, no refetch on focus), lists keep the previous page while the next loads,
mutations invalidate `<ENTITY>_KEYS.ALL`, switching organisation clears the cache.

### Tests (`apps/web`)
vitest + testing-library; `src/__tests__/helpers.tsx` has `mockFetch`, `route`, `searchPage`, `lastBody`,
`renderWithQuery`; `router-mock.ts` replaces `next/navigation`.

## Entry points
- API: `apps/api/app/main.py` (`uvicorn app.main:app`), routes under `/api`, docs `/api/docs`
- Worker: `apps/api/app/worker/main.py`
- Web: `apps/web` (`next start`, standalone output)
- Compose: `docker-compose.yml` (+ `docker-compose.dev.yml` for ports 55442 / 59100 / 58100)
- Verification: `scripts/verify.sh <tests...>` — API: `lint-imports` then pytest in the api-test image; web: vitest

## Conventions
- Tenancy: every tenant table has `organization_id`; handlers get it from the `Actor`, never from the client.
- IDs: UUID v4; timestamps `timestamptz`.
- `QuestionView` is the only question renderer; MathType formulas arrive as LaTeX.
