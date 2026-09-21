---
generated: 2026-09-21
repo_root: examind
generator: discover_generic + greenfield layout (hand-written)
verified_by: Loc Tran (blanket pre-approval in chat, 2026-09-21 — confirm at final review)
---

# Architecture map — Examind

Greenfield repo: discovery found no packages. This map records the **target layout** every
`touches` path must follow. Paths below do not exist yet; tickets mark them `# new`.

## Packages

| Name | Path | Ecosystem | Role |
|---|---|---|---|
| examind-api | `apps/api` | python 3.12 (uv, FastAPI, SQLAlchemy 2, Alembic) | HTTP API, auth, domain services |
| examind-worker | `apps/api` (same package, entry `app/worker/main.py`) | python | Postgres-queue job runner: ingestion, stats refresh |
| examind-web | `apps/web` | node 24, Next.js 15 App Router, TS, Tailwind | UI for super_admin / org_admin / teacher / student |
| infra | `infra/`, `docker-compose*.yml` | docker | Caddy, backups, deploy |

Worker shares the API package so models/services are imported, never duplicated.

## Backend layout (`apps/api/app`)

| Path | Layer | Convention |
|---|---|---|
| `app/core/` | infra | config (`pydantic-settings`), db session, security (jwt, argon2), errors, storage (S3/MinIO) |
| `app/models/<entity>.py` | data | SQLAlchemy 2 typed models, one module per aggregate |
| `app/schemas/<area>.py` | api | Pydantic request/response DTOs |
| `app/services/<area>.py` | domain | business rules; every query filtered by `organization_id` |
| `app/routers/<area>.py` | api | FastAPI routers, thin: validate → service → schema |
| `app/deps.py` | api | `current_user`, `require_role(...)`, `org_scope` dependencies |
| `app/ingestion/` | worker | parsers (docx/pdf/ocr), splitter, llm, tagging |
| `app/worker/` | worker | job queue (`jobs` table, SKIP LOCKED), handlers |
| `app/seed/` | data | seed data (system org, super admin, Toán GDPT 2018 topic tree) |
| `migrations/versions/` | data | Alembic revisions |
| `tests/` | test | pytest, real Postgres from compose (`ltree`, `pgvector`) |

## Frontend layout (`apps/web/src`)

| Path | Layer | Convention |
|---|---|---|
| `app/(auth)/login/page.tsx` | web | public routes |
| `app/(app)/<area>/page.tsx` | web | authenticated routes, role-gated in layout |
| `components/ui/` | web | shared primitives (button, input, table, dialog) |
| `components/<area>/` | web | feature components (e.g. `question/QuestionView.tsx`) |
| `lib/api.ts` | web | fetch wrapper, cookie auth, typed errors |
| `lib/types.ts` | web | DTO types mirrored from API schemas |
| `tests/` / `*.test.tsx` | test | vitest + testing-library; `e2e/` Playwright |

## Entry points

- API: `apps/api/app/main.py` (`uvicorn app.main:app`), routes under `/api`
- Worker: `apps/api/app/worker/main.py`
- Web: `apps/web` (`next start`, standalone output)
- Compose: `docker-compose.yml` (+ `docker-compose.dev.yml`)
- Verification: `scripts/verify.sh <tests...>` dispatches `apps/api/tests/*` → pytest, `apps/web/*` → vitest

## Conventions decided (not observed — repo is new)

- Tenancy: every tenant table has `organization_id UUID NOT NULL`; services receive an `OrgScope` and never query without it.
- IDs: UUID v4; timestamps `timestamptz`.
- Errors: `AppError(code, http_status, message)` → JSON `{error: {code, message}}`.
- Auth: login by `org_code + username + password`; access JWT (15 min) + refresh token (30 days, hashed in DB) in httpOnly cookies.
- Shared reuse: `QuestionView` is the only question renderer.

## Gaps settled

- Domain code lives in `app/services`; no separate domain package (small team, one service).
- No DI container: FastAPI dependencies.
- External contracts: none signed off; all APIs are internal to this repo.
