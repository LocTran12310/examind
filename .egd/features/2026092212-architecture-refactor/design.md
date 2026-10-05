---
feature: architecture-refactor
adr_count: 7
---

# Logical design

## Approach
Vertical slices: each bounded context moves API and web together, old and new code live side by side until the last
slice deletes the old folders. No database change.

**API** (`apps/api/app`)
```
main.py                        composition root (includes each module's interface router)
shared/
  domain/         errors.py (DomainError: NotFound, Conflict, Invalid, Forbidden, Unauthenticated), clock.py, ids.py
  application/    search.py (SearchRequest, Filter, SortKey, Page), unit_of_work.py (UnitOfWork port), actor.py (Actor)
  infrastructure/ db.py (engine, session, registry), schema/<area>.py (Table objects — the one physical schema),
                  sql_search.py (filters/sort/paging → SQL), sql_unit_of_work.py, storage.py, security.py, …
  interface/      errors.py (DomainError → HTTP), request_id.py, deps.py (actor, uow), search_schemas.py
modules/<context>/
  domain/         entities.py (dataclasses), value_objects.py, errors.py, ports.py (Protocol), services/ (pure rules)
  application/    commands/<verb>_<noun>.py, queries/<name>.py (one handler each, ports in the constructor), dto.py, api.py
  infrastructure/ orm.py (map_imperatively onto shared tables), repositories.py, read_models.py, adapters/
  interface/      router.py (thin), schemas.py (Pydantic), deps.py (builds handlers)
```
Contexts: identity, academic, taxonomy, bank, ingestion, assessment, analytics, audit.

**Web** (`apps/web/src`)
```
app/                             routes only; page.tsx renders a page component
components/ui/                   shadcn CLI output
components/common/               shared composites (DataTable, FormDialog, OptionSelect, DatePicker, Markdown, …)
components/layout/               shell, sidebar, switchers, page header
components/page-components/<Page>/<Component>/<Component>.tsx
hooks/common/                    use-table-query (URL state), use-save-shortcut, use-debounce, use-mobile
hooks/react-query/use-query-<domain>.ts
hooks/page-hooks/<page>/use-<page>-*.ts
services/<module>.service.ts     the only callers of lib/common/http
stores/common/, stores/page-stores/<page>/   zustand (UI state only)
constants/  dtos/  interfaces/  types/
lib/common/                      http.ts, query-client.ts, search-body.ts, datetime.ts, list-memory.ts
lib/page-libs/<page>/            pure helpers of one page
```

## Alternatives considered
| Option | Why not |
| --- | --- |
| Declarative ORM models as the domain | Rules would depend on SQLAlchemy; the dependency rule could not be linted |
| Separate domain classes + hand mappers for every table | Twice the code for CRUD modules with no rule to protect |
| Big-bang rewrite | Nothing runnable for days; regressions found late |
| Vite + client router | Loses server session check and the existing build; not requested |

## Domain model
Unchanged tables. Domain entities are dataclasses mapped imperatively onto the same tables.

## Contracts
| Method & path | Notes |
| --- | --- |
| `POST /api/<resource>/search` | body `{page, limit, q?, sort?: [{field, desc}], filters?: {<field>: {operator?, value?, from?, to?}}, …resource params}` → `{data, total, page, limit}` |
| errors | `{code, message, details: {fields?, requestId}}` + `X-Request-Id` |
| other routes | unchanged paths; list GETs removed per context |

## State ownership
| State | Owner | Lifetime |
| --- | --- | --- |
| Server data | React Query cache | until invalidated / org switch |
| Table filters, sort, page | URL | navigation |
| Chosen school year / subject | zustand store (persisted per org) | browser |

## Failure modes
| Condition | Code | HTTP | UI |
| --- | --- | --- | --- |
| Entity missing in the org | `not_found` | 404 | toast / empty state |
| Duplicate | `conflict` | 409 | field error |
| Rule broken | `validation_error` | 422 | field error |
| Bad filter / sort | `bad_filter` / `bad_sort` | 422 | toast |
| Not allowed | `forbidden` | 403 | toast |
| No session | `unauthenticated` | 401 | refresh then login |

## Observability
Every response carries `X-Request-Id`; errors repeat it in `details.requestId`; the access log prints it.

## ADRs

### ADR-01 — Dataclass entities mapped imperatively on a shared physical schema
**Context:** Domain code must not import the ORM; one Postgres database serves every context.
**Decision:** `shared/infrastructure/schema/*` holds the `Table` objects (the physical schema, also Alembic's metadata).
Each module maps its own dataclasses onto them in `infrastructure/orm.py`. Read models may join any table through
SQLAlchemy Core; a command that needs another context's data calls that context's `application/api.py`.
**Consequences:** No mapper boilerplate; queries keep `Entity.column` expressions; cross-context writes are explicit.
**Status:** accepted

### ADR-02 — Commands through repositories and a unit of work, queries through read models
**Context:** Writes need rules and one transaction; lists need joins and counts.
**Decision:** Command handlers load/save aggregates through repository ports and call `uow.commit()`.
Query handlers call read-model ports that return DTOs.
**Consequences:** Transactions are explicit per use case; search SQL stays in one place per context.
**Status:** accepted

### ADR-03 — Search endpoint with typed filters
**Context:** Lists need operators, ranges, enums and a documented body.
**Decision:** `POST /<resource>/search`; each filter is `{operator?, value?, from?, to?}` read by the column kind:
text (`* = + - !`), number/date/day (`= < <= > >=` or from/to), enum/uuid/bool (`value`, a list = any of).
Sorting by several columns and `q` stay. Answer `{data,total,page,limit}`, `limit` ≤ 200 (1000 for pickers).
**Consequences:** One validator for every list; the URL keeps the web state and is converted to the body.
**Status:** accepted

### ADR-04 — Error body and request id
**Context:** One error shape for every failure and a way to find it in logs.
**Decision:** `{code, message, details: {fields?, requestId}}`; middleware sets `X-Request-Id` (echoes a valid incoming one).
**Consequences:** The web reads `details.fields` for forms.
**Status:** accepted

### ADR-05 — Dependency rules are linted
**Context:** A layer rule that is not checked erodes.
**Decision:** `import-linter` contracts (layers per module, forbidden framework imports in domain, modules talk through
`application`, shared never imports modules) run in `scripts/verify.sh`; ESLint restricts imports on the web side.
**Consequences:** A wrong import fails the build.
**Status:** accepted

### ADR-06 — React Query owns server state
**Context:** Hand-written fetch hooks refetch by hand and cache nothing.
**Decision:** One QueryClient (staleTime 0, retry 1, no refetch on focus); keys in `constants/react-query-key.constant.ts`
(`<ENTITY>_KEYS`, first element = resource); lists use `keepPreviousData`; mutations invalidate `<ENTITY>_KEYS.ALL`;
switching organisation clears the cache.
**Consequences:** No `reloadKey`; fewer duplicate requests.
**Status:** accepted

### ADR-07 — snake_case JSON and cookie sessions stay
**Context:** A contract change was allowed, but renaming every field brings no value.
**Decision:** Keep snake_case and httpOnly cookies.
**Consequences:** DTO types keep their field names.
**Status:** accepted
