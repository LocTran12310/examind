---
feature: platform-foundation
adr_count: 8
---

# Logical design — Platform foundation

## Approach
One Docker Compose runs `postgres` (pgvector image, `ltree` + `vector` + `citext` extensions),
`minio`, `api` (FastAPI, runs Alembic + idempotent seed on boot), `web` (Next.js standalone)
and `caddy` (routes `/api/*` → api, everything else → web, so cookies are same-origin).
The API is a layered monolith: routers → services → SQLAlchemy models. Every tenant table has
`organization_id`; routers obtain an `OrgScope` from the authenticated user and pass it to
services, which always filter by it. Auth is cookie-based JWT issued by the API; the web app
never stores tokens in JS. The web app uses server components for layout/role gating (reads
`/api/auth/me` with forwarded cookies) and client components for forms.

## Alternatives rejected
| Option | Why not |
| --- | --- |
| Supabase / BaaS auth | Vendor lock-in; user chose fully self-hosted compose (chat, 2026-09-21) |
| Postgres RLS for tenancy | Harder to test and to debug; service-layer scoping plus isolation tests is enough for one API |
| Bearer tokens in localStorage | XSS-exposed; same-origin httpOnly cookies via Caddy are simpler |
| Adjacency list only for topics | Roll-up stats need subtree queries; `ltree` makes `path <@ x` indexed |
| Separate worker package | Would duplicate models; worker is a second entry point of the api package |

## Domain model
| Entity | Fields | Notes |
| --- | --- | --- |
| `Organization` | id, code (citext unique), name, status active/suspended, is_system, settings jsonb, created_at, deleted_at | code is the human key |
| `User` | id, organization_id, username (citext), password_hash, full_name, email?, role, is_active, must_change_password, failed_logins, locked_until, last_login_at | unique (organization_id, username) |
| `RefreshToken` | id, user_id, token_hash, expires_at, revoked_at | rotated on refresh |
| `AuditLog` | id, organization_id, actor_id, action, target_type, target_id, data jsonb, created_at | org/user CRUD, password resets |
| `SchoolClass` | id, organization_id, name, grade, school_year | unique (org, name, school_year) |
| `ClassMember` | class_id, user_id | PK both |
| `Subject` / `Grade` / `Semester` | id, organization_id, code, name, sort | seeded per org |
| `Topic` | id, organization_id, subject_id, parent_id, name, slug, level_kind, path ltree, sort | GiST index on path |
| `Tag` | id, organization_id, group, name | unique (org, group, lower(name)) |
| `Question` (minimal) | id, organization_id, type, stem, options jsonb, answer jsonb, solution, difficulty, status | full lifecycle in later features; here only for `QuestionView` preview |
| `Asset` | id, organization_id, storage_key, mime, width, height | images in MinIO, referenced as `asset:<id>` in markdown |

## Contracts
All under `/api`, JSON, errors `{ "error": { "code": str, "message": str, "fields"?: {..} } }`.

| Method & path | Role | Body / query → response |
| --- | --- | --- |
| `GET /health` | public | → `{status, db, storage}` |
| `POST /auth/login` | public | `{org_code, username, password}` → `{user}` + cookies; 401 `invalid_credentials`, 403 `org_suspended`, 429 `locked` |
| `POST /auth/refresh` | cookie | → 204 + new cookies; 401 |
| `POST /auth/logout` | auth | → 204, revokes refresh |
| `GET /auth/me` | auth | → `{id, username, full_name, role, must_change_password, org:{id,code,name}}` |
| `POST /auth/change-password` | auth | `{current_password, new_password}` → 204 |
| `GET/POST /admin/orgs`, `GET/PATCH/DELETE /admin/orgs/{id}`, `POST /admin/orgs/{id}/suspend|activate` | super_admin | org CRUD; create returns `{org, admin:{username, temp_password}}`; `DELETE ?hard=true` |
| `GET/POST /users`, `GET/PATCH /users/{id}`, `POST /users/{id}/reset-password` | org_admin, teacher (students only) | paging `?q=&role=&class_id=&page=` |
| `POST /users/import/preview`, `POST /users/import/commit` | org_admin, teacher | multipart CSV/XLSX → `{rows:[{row, full_name, username, role, class, errors[]}]}`; commit → `{created:[{username, full_name, temp_password}]}` |
| `GET/POST /classes`, `GET/PATCH/DELETE /classes/{id}`, `POST/DELETE /classes/{id}/members` | org_admin, teacher | |
| `GET /taxonomy` | auth | → `{subjects, grades, semesters}` |
| `GET /topics?subject_id=` | auth | → flat list with `path`, `parent_id`, `depth` |
| `POST /topics`, `PATCH /topics/{id}` (name, parent_id, sort), `DELETE /topics/{id}`, `POST /topics/{id}/merge` `{target_id}` | org_admin, teacher | |
| `GET/POST /tags`, `PATCH/DELETE /tags/{id}` | auth read; org_admin, teacher write | |
| `POST /assets` (multipart), `GET /assets/{id}` | auth | stream from MinIO with org check |
| `GET /questions/{id}` | auth | minimal, for preview |

## State ownership
| State | Owner | Lifetime |
| --- | --- | --- |
| Session | httpOnly cookies `ex_access`, `ex_refresh` | 15 min / 30 days |
| Current user | `/auth/me`, fetched in `(app)/layout.tsx` server component | request |
| Last org code | `localStorage["examind.org_code"]` | browser |
| Import preview rows | client state of import page | page |

## Error taxonomy
| Condition | Code | HTTP | UI |
| --- | --- | --- | --- |
| Bad credentials / inactive user | `invalid_credentials` | 401 | generic login message |
| Org suspended / deleted | `org_suspended` | 403 | "Tổ chức đang bị khóa" |
| Locked out | `locked` | 429 | "Thử lại sau N phút" |
| Not authenticated / expired | `unauthenticated` | 401 | web refreshes once, then redirects to /login |
| Wrong role | `forbidden` | 403 | toast |
| Other org's id | `not_found` | 404 | not-found state |
| Validation | `validation_error` | 422 | field errors |
| Unique conflict (code, username, tag) | `conflict` | 409 | field error |
| Topic has children | `topic_has_children` | 409 | inline message |
| Password must change | `password_change_required` | 403 | redirect to /change-password |

## Cache & offline
No offline mode. Web pages are dynamic (`no-store`); taxonomy lists are fetched per page.

## Observability
Structured JSON logs (structlog) with request id, org code, user id; never passwords or tokens.
Audit log rows for org create/update/suspend/delete, user create/import/reset/deactivate.

## ADRs

### ADR-01 — Self-host everything in one Docker Compose
**Context:** Free-first; must run identically on a Mac and an Oracle ARM VM.
**Decision:** Compose with postgres, minio, api, web, caddy (+ worker, ollama in later features); no BaaS. All config via env.
**Consequences:** We own backups and upgrades; moving hosts is `git clone` + `.env` + `docker compose up`.
**Status:** accepted

### ADR-02 — Org-code login with per-org usernames
**Context:** Students often lack email; centers want short usernames.
**Decision:** Login key is (org code, username); `organization_id` UUID stays the internal FK; code editable.
**Consequences:** Login form has three fields; renaming a code does not touch data but users must learn the new code.
**Status:** accepted

### ADR-03 — Tenancy enforced in the service layer
**Context:** One API, small team.
**Decision:** `OrgScope` dependency; every service query filters `organization_id`; cross-org ids return 404; isolation covered by tests.
**Consequences:** A forgotten filter is a leak, so isolation tests are part of each list/get endpoint's done-when.
**Status:** accepted

### ADR-04 — Topics as `ltree` materialised paths
**Context:** Stats must roll up from "Nguyên hàm từng phần" to "Giải tích".
**Decision:** `topics.path ltree` built from slugs of ids (`t<short-id>` labels) plus `parent_id`; move/merge rewrite subtree paths in one transaction.
**Consequences:** Subtree queries are indexed; moves are O(subtree size) writes.
**Status:** accepted

### ADR-05 — Cookie JWT through a same-origin reverse proxy
**Context:** Web and API are separate containers.
**Decision:** Caddy serves both under one origin; API sets httpOnly SameSite=Lax cookies; refresh tokens are opaque, hashed, rotated.
**Consequences:** No CORS in production; dev uses the same Caddy entry at http://localhost:8080.
**Status:** accepted

### ADR-06 — Web tests outside route-group folders
**Context:** Ticket `tests:` paths are substituted into a shell command; `(auth)`/`(app)` route-group parentheses break it.
**Decision:** Page-level tests live in `apps/web/src/__tests__/`; component tests sit next to components. Pages export only the default component; reusable pieces move to `src/components/`.
**Consequences:** Next.js page export rules and the evidence runner are both satisfied.
**Status:** accepted

### ADR-07 — Raster images only; SVG uploads rejected
**Context:** Assets are served from the app origin; SVG can carry script.
**Decision:** Accept PNG/JPEG/GIF/WEBP by magic-byte sniffing, `X-Content-Type-Options: nosniff`, org-checked `GET /api/assets/{id}`. Demo images are generated by a tiny stdlib PNG writer (no Pillow in the API image).
**Consequences:** Math/figures in future ingestion must be rasterised or converted to LaTeX.
**Status:** accepted

### ADR-08 — Dev ports and compose override
**Context:** 8080, 55432, 59000 were taken on the dev machine by other stacks.
**Decision:** Caddy on 8088/8448; dev override exposes Postgres 55442, MinIO 59100/59101, API 58100; local `.env` sets `COMPOSE_FILE=docker-compose.yml:docker-compose.dev.yml`; the VM omits the override.
**Consequences:** Tests and the running stack share one Postgres container (separate `examind_test` DB).
**Status:** accepted
