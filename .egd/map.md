# Repository map

reviewed_by: Loc Tran (blanket pre-approval in chat, 2026-09-22 — confirm at final review)

<!-- imported from .ai/architecture.md -->

---
generated: 2026-09-22
repo_root: examind
generator: hand-written from the repo (architecture-refactor F13, final state after UOW-07)

---

# Architecture map — Examind

Monorepo: `apps/api` (FastAPI, SQLAlchemy 2, Alembic, Postgres + ltree/pgvector, MinIO), the worker (same
package), and `apps/web` (Next.js App Router, React 19, shadcn/ui, TanStack Query + Table, zustand).
Compose runs postgres, minio, api, worker, web and caddy (:8088).

## Backend (`apps/api/app`)

```
main.py                         composition root: error handlers, request id, actor resolver, cross-module wiring, routers
metadata.py                     every table + every module's ORM mapping (Alembic, bootstrap, tests import it)
shared/                         shared kernel — no business rules
  domain/                       errors.py (DomainError, NotFound, Conflict, Invalid, Forbidden, Unauthenticated…), clock.py, ids.py,
                                text.py, images.py (sniff), answers.py, question_quality.py (rules ingestion and bank share)
  application/                  search.py (SearchRequest, Filter, SortKey, Page), unit_of_work.py, actor.py (Actor), audit.py
                                (AuditTrail port), calendar.py (BusinessCalendar port), jobs.py
  infrastructure/               config.py (settings), logging.py, storage.py (S3), timezone.py (business days), png.py,
                                db.py (engine, session, mapper_registry, metadata), schema/<area>.py (every Table + Index),
                                sql_search.py (filters/sort/paging → SQL), sql_unit_of_work.py, sql_audit.py, sql_jobs.py, calendar.py
  interface/                    errors.py, request_id.py, auth.py (current_actor, staff_actor), deps.py, search_schemas.py
modules/<context>/              the 8 bounded contexts below
  domain/                       entities.py (dataclasses), value_objects.py, errors.py, ports.py (Protocol), services/ (pure rules)
  application/                  commands/<verb>_<noun>.py, queries/<name>.py — one handler class each, ports in __init__;
                                dto.py (frozen dataclasses), ports.py (read ports), common.py, api.py (what other modules may call)
  infrastructure/               orm.py (map_imperatively onto shared tables), repositories.py (Sql*Repository),
                                read_models.py (Sql*Reader: search/facets/reports), adapters/ (other modules' APIs, LibreOffice, LLM, OCR, S3…)
  interface/                    router.py (thin), schemas.py (Pydantic in/out), deps.py (builds handlers from adapters)
worker/                         job loop (queue.py); handlers.py wires the modules like main.py; each job type calls an application command
seed/                           system org, super admin, per-org reference data, demo question (composition level)
```

### The modules

| Module | Owns | Tables (`shared/infrastructure/schema/…`) |
| --- | --- | --- |
| `identity` | login (lockout, IP throttle), refresh rotation, logout, switch-org, change password, `/auth/me`, `/me/orgs`; users of an org (CRUD, reset password, link/unlink, CSV/XLSX import); organisations and memberships (platform admin); the actor resolver | identity: organizations, users, organization_members, refresh_tokens |
| `academic` | school years + terms + rollover, classes + members, structure (school levels › grades › classes, `Grade` and `SchoolLevel` entities), student record | academic: school_years, school_terms, classes, class_members (grades, school_levels sit in taxonomy.py) |
| `taxonomy` | subjects, semesters, the topic tree (create, rename, move, merge, delete), tags | taxonomy: subjects, semesters, topics, tags, grades, school_levels |
| `bank` | the Question aggregate (content, topics, tags), review actions, answer key, approve-confident, reviewer assignment, key audit, triage and near-duplicates, facets | bank: questions, question_topics, question_tags, review_events |
| `ingestion` | uploads (duplicate check), the pipeline (extract → header → split → AI → persist → triage → topic), re-parse, document meta, assets, AI models, processing settings | ingestion: source_documents, assets, ai_models; jobs |
| `assessment` | exams (blueprint, order, points, from a document, personal review exams), assignments, attempts (start, save, submit, grace, sweep), THPT 2025 grading, answer facts, assignment report | assessment: exams, exam_questions, assignments, assignment_targets, attempts, attempt_answers, answer_facts |
| `analytics` | reports over answer facts (topic tree, groups by type/difficulty/tag, class heatmap), topic mastery (fed by assessment's facts, rebuilt by replay), personal practice and class review plans | analytics: student_topic_mastery (reads answer_facts) |
| `audit` | the history list (`POST /audit/search`); every module writes history through the shared `AuditTrail` port | audit: audit_logs |

Cross-module calls (all through `application/api.py`, adapters wired in `main.py` and `worker/handlers.py`):
identity → academic (class directory for the import); bank → taxonomy (topic/tag checks), identity (reviewers);
ingestion → bank (parsed questions, triage, kNN topic), taxonomy (source tags), assessment (exam from a document);
assessment → bank (questions, pool, classification), academic + identity (roster, snapshots), taxonomy (subjects),
analytics (answer facts → mastery); analytics → academic + identity (class members), assessment (personal exams,
assignments, attempts); bank ← assessment (a question an exam uses is kept).

### Rules (linted: `.importlinter`, `tests/test_architecture.py`)
- Inside a module: `interface → infrastructure → application → domain`; nothing points outward.
- `domain` imports no sqlalchemy / fastapi / pydantic / boto3 / starlette and nothing from `shared.application|infrastructure|interface`.
- `application` imports no framework or adapter; it sees ports (Protocol) and dataclasses only.
- A module imports another module's `application` only (usually `application/api.py`), never its domain,
  infrastructure or interface.
- `shared` never imports `modules` or the composition root (`main`, `metadata`, `worker`, `seed`).
- Every module has the four layers and is listed in the layers contract; the old packages (`routers`, `services`,
  `models`, `schemas`, `core`, `deps.py`) do not exist.
- The metadata matches the migrations: `alembic check` finds nothing (`tests/test_schema_drift.py`); indexes on
  expressions are left out of the comparison (`migrations/env.py`).

### How a request flows
`router` (Pydantic body → command/query dataclass) → `Depends(deps.<handler>)` builds the handler with
`Sql*Repository(db)`, `Sql*Reader(db)`, `SqlUnitOfWork(db)` and the registered adapters of other modules → handler
applies the rules and calls `uow.commit()` → router maps the returned DTO to the response schema.
The caller is an `Actor` (`current_actor` / `staff_actor`); every repository and reader filters by `actor.org_id`.
Grading example: `SubmitAttempt` → `Grading` writes answer facts → `FactListener` (analytics adapter) →
`AnalyticsApi.answer_recorded` → `RecordAnswer` moves the topic mastery in the same transaction.

### Contracts
- Lists: `POST /api/<resource>/search`, body `{page, limit, q?, sort?: [{field, desc}], filters?: {<field>: {operator?, value?, from?, to?}}, …resource params}`
  → `{data, total, page, limit}`. Filter reading by column kind: text `* = + - !`; number/date/day `= < <= > >=`
  or `from`/`to`; enum/uuid/bool `value` (list = any of). Unknown field/operator → 422 `bad_filter`, bad sort → `bad_sort`.
  Plain lists kept as they were: `/me/orgs`, `/me/assignments`, `/me/practice`, `/me/mastery`, `/classes/{id}/overview`;
  reports stay `GET /stats/topics|groups|heatmap` with query parameters.
- Errors: `{code, message, details: {fields?, requestId}}` + `X-Request-Id` header; malformed ids are 422.
- Days are business days (Asia/Ho_Chi_Minh); timestamps stored and sent in UTC.
- JSON stays snake_case; sessions are httpOnly cookies (15 min access JWT, 30 day refresh).

### Tests (`apps/api/tests`)
- HTTP tests per resource (`test_<area>_api.py`) against a real Postgres (`scripts/verify.sh`).
- `tests/unit/` — handlers against in-memory fake ports, no database (one file per module; the audit handler sits in
  `test_analytics_handlers.py`).
- `test_architecture.py` — dependency rules, the eight modules, the old layout gone; `test_schema_drift.py` — `alembic check`.
- `test_golden_official.py` — the 18 official files (needs `EXAMIN_DIR`).

## Frontend (`apps/web/src`)

```
app/                                   routes only: page.tsx renders one page component; (app)/layout.tsx checks the session (getMe)
components/ui/                         shadcn CLI output, never edited
components/common/<Name>/<Name>.tsx    shared composites: DataTable/, FormDialog, FormField, DatePicker, OptionSelect, HistoryPanel,
                                       QuestionView, TopicStatsTree, GroupStats, PracticeButton, TopicTreeSelect, …
components/layout/<Name>/<Name>.tsx    Providers, AppShell, AppSidebar, OrgSwitcher, UserMenu, YearSwitcher, ThemeProvider, ThemeToggle
components/page-components/<Page>/<Page>Page.tsx and <Page>/<Component>/<Component>.tsx
hooks/common/                          use-table-query (table state in the URL), use-me, use-year, use-practice-button, …
hooks/react-query/use-query-<domain>.ts   useXxxQuery / useXxxSearchQuery / useXxxMutation — call services only
hooks/page-hooks/<page>/use-<page>-*.ts(x)  state and logic of one page (columns, dialogs, submit)
services/<module>.service.ts           `export const xService = {…}` — the only callers of lib/common/http
stores/common/, stores/page-stores/<page>/   zustand, UI state only (never server data)
constants/                             *.constant.ts; react-query-key.constant.ts holds <ENTITY>_KEYS
dtos/ (*.dto.ts request bodies) · interfaces/ (*.interface.ts entities, pages) · types/ (*.type.ts unions)
lib/common/                            http.ts, query-client.ts, search-body.ts, form-errors.ts, datetime.ts, dates.ts, list-memory.ts,
                                       nav.ts, session.ts, topic-tree.ts, topic-selection.ts, exam-period.ts, csv.ts, …
lib/page-libs/<page>/                  pure helpers of one page
lib/utils.ts                           shadcn `cn`
```

### Rules (ESLint `no-restricted-imports` / `no-restricted-globals` / `no-restricted-syntax`, `src/__tests__/architecture.test.ts`)
- Only `services/**` import `http` from `lib/common/http` (components may use the `ApiError` class).
- Only `hooks/react-query/**` (plus `lib/common/query-client`, `components/layout/Providers`, tests) import `@tanstack/react-query`.
- `app/**` imports neither services nor query hooks; every `page.tsx` imports one page component (or only redirects).
- `components/**` and `hooks/page-hooks/**` never call `fetch`.
- `components/common/**` never imports a page component.
- The old layout stays gone: `@/lib/hooks`, `@/lib/api`, `@/lib/types`, `@/components/app/*`, `@/components/data-table/*`
  are forbidden imports; `components/` holds only ui, common, layout, page-components; no `useApi` anywhere.
- shadcn components are imported one file each; no native `<select>` or date inputs (OptionSelect, DatePicker).
- Named exports only, no barrel files; hooks `use-*.ts` (kebab-case), component folders PascalCase.

### Data flow
URL (filters, sort, page) → `useTableQuery` → `toSearchBody` → `useXxxSearchQuery(body)` →
`xService.search(body)` → `POST /api/x/search`. React Query owns server state: one QueryClient
(staleTime 0, retry 1, no refetch on focus), lists and reports keep the previous answer while the next loads,
mutations invalidate `<ENTITY>_KEYS.ALL` (plus what they move, e.g. a class review refreshes the class overview),
switching organisation clears the cache.

### Tests (`apps/web`)
vitest + testing-library; `src/__tests__/helpers.tsx` has `mockFetch`, `route`, `searchPage`, `lastBody`, `lastQuery`,
`renderWithQuery`; `router-mock.ts` replaces `next/navigation`; `architecture.test.ts` checks the folder rules.

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
