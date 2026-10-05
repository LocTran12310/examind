# Layered API modules and a query-driven web client

## Problem
Loc Tran (chat, 2026-09-22) asked to restructure the whole project: the web app must use React Query and a
standard folder layout (routes → page components → page hooks → query hooks → services), and the API must
follow clean architecture with every module split into domain / application / infrastructure / interface.
Today the web fetches with a hand-written `useApi` (94 uses, manual `reloadKey`/`reload()` refreshes, no cache)
and the API is split horizontally (routers / services / models / schemas) with services talking to SQLAlchemy
directly, so business rules, persistence and HTTP are mixed and nothing enforces a dependency direction.

## Outcome
---
feature: architecture-refactor
slug: 2026092212-architecture-refactor
owner: Loc Tran
created: 2026-09-22
status: approved
---

## Success signal
`lint-imports` and ESLint boundary rules pass with zero exceptions; `useApi` has 0 uses; every list calls
`POST …/search`; the full API suite, the 18-paper official golden set and the web suite pass with the same
behaviour as before.

## Out of scope
- Database schema changes
- camelCase JSON, token storage changes, idempotency keys (no Redis in the stack)
- New product features

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Developer (Loc Tran) | Logic spread over pages, services mix SQL and rules | One place per concern; lint refuses a wrong import |
| Every user | Lists refetch by hand, duplicate requests, full reload on org switch | Cached queries, invalidation after writes, instant org switch |

## Constraints
| Kind | Detail |
| --- | --- |
| Framework | Next.js App Router stays; FastAPI + SQLAlchemy + Alembic stay |
| UI | components/ui stays shadcn CLI output |
| Docs | Conventions are written as Examind's own standard; no external project is named |
