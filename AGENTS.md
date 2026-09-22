# Examind — working agreement

Ngân hàng câu hỏi và đề ôn luyện cho trung tâm/giáo viên, self-hosted. Monorepo:
`apps/api` (FastAPI + SQLAlchemy + Alembic, Postgres/pgvector, MinIO, worker) và `apps/web`
(Next.js App Router, React 19, shadcn/ui, TanStack Query + Table, zustand). Caddy phục vụ cả hai ở `:8088`.

This file is the contract every agent (Codex, Claude Code, an IDE assistant) follows in this repo.
`apps/api/AGENTS.md` and `apps/web/AGENTS.md` add the rules of each side. The full map is
[`.ai/architecture.md`](.ai/architecture.md) — read it before the first change in a new area.

## Ground rules

1. **The architecture map is binding.** New code goes into the layout it describes; the old flat layout no
   longer exists and must not come back.
2. **Layer boundaries are linted, not suggested.** `lint-imports` (API) and ESLint import rules (web) fail
   the build on a wrong import. Never weaken a rule to make code fit; change the code.
3. **Tests are the evidence.** A change is done when the suite it touches passes — locally, not "should pass".
   State failures plainly; never describe an unrun check as green.
4. **Behaviour stays unless asked.** Refactors keep responses, rules and numbers identical; anything that
   changes on the way is reported and recorded.
5. **Write like the file you are in.** Same comment density, same naming, Vietnamese in user-facing strings,
   English in code and docs. No decorative comments, no restating the obvious.
6. **No external project is ever named** in code, comments, docs or commit messages. Conventions here are
   Examind's own.
7. **Never run destructive commands on live data** (drop/truncate, mass delete, history rewrite, deleting
   MinIO objects) without the owner asking for that exact action. Back up first: `pg_dump` into `backups/`.
8. **Secrets stay out of the repo.** `.env` is ignored; `.env.example` documents every variable.

## Commands

```bash
make up                 # build + start the whole stack (http://localhost:8088)
make dev                # postgres + minio with host ports (55442 / 59100) for local api & web
make api-dev            # uvicorn --reload on :58100 (needs `make dev`)
make web-dev            # next dev on :3000, /api proxied to :58100
make test               # API suite (docker) + web suite
make test-api           # ruff + lint-imports + pytest inside the api-test image
make test-web           # tsc + eslint + vitest
make golden             # the 18 official exam papers (needs EXAMIN_DIR)
make migrate            # alembic upgrade head
make revision m="..."   # new Alembic revision (autogenerate)
make fmt                # ruff --fix on the API
```

`scripts/verify.sh <paths…>` runs exactly the tests named (API paths run in docker, web paths in vitest);
it is what the plan controller records as evidence.

## Conventions that apply everywhere

- **Contract**: lists are `POST /api/<resource>/search` with
  `{page, limit, q?, sort?: [{field, desc}], filters?: {<field>: {operator?, value?, from?, to?}}, …resource params}`
  and answer `{data, total, page, limit}`. Errors are `{code, message, details: {fields?, requestId}}` plus an
  `X-Request-Id` header. JSON is snake_case.
- **Tenancy**: every query is scoped by the caller's organisation (`Actor.org_id`), never by a client-supplied id.
- **Time**: timestamps are stored and sent in UTC; days are business days (`Asia/Ho_Chi_Minh`).
- **Naming**: Python `snake_case`, TypeScript `camelCase` values / `PascalCase` components /
  kebab-case file names for hooks, services, stores and constants.
- **Commits**: `type(scope): summary` (`feat`, `fix`, `refactor`, `docs`, `test`, `chore`), body explains why.
  Commit only when the work runs; never commit a red suite.

## Planning (AI-DLC)

Feature work is planned on disk under `.ai/features/YYYYMMDDNN-<slug>/` and gated by
`scripts/aidlc` (Inception → Construction → Operations). Before touching a planned feature run
`./scripts/aidlc -d .ai/features/<slug> status` and follow it; never hand-edit `.aidlc-state.yaml`.
`scripts/gen_plan.py` writes the UoW/ticket files from `plan_spec.py`;
`scripts/close_ticket.sh <feature-dir> T-xx-yy` closes a ticket and records a real test run.
Decisions live in `03-logical-design.md` (ADRs) and `.ai/final-review.md`.

## Skills

Task recipes live in `.agents/skills/<name>/SKILL.md` (Claude Code reads the same files through
`.claude/skills`). Load the one that matches before starting:

| Skill | When |
| --- | --- |
| `api-endpoint` | add or change an API use case / endpoint inside a module |
| `api-search` | add a list resource (search contract, filters, facets) |
| `web-screen` | add or change a screen: service → query hook → page hook → page component |
| `db-change` | a table, column or index changes (schema + migration + drift check) |
| `ingestion-change` | anything touching the document pipeline (golden set must not move) |
| `feature-plan` | start a new planned feature through the AI-DLC controller |
