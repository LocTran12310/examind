# Demo evidence — architecture-refactor

## UOW-01 foundation + Tags (2026-09-22)
- `lint-imports`: 4 contracts kept (module layers, pure domain, pure application, shared kernel);
  `tests/test_architecture.py` also checks that modules only import each other's `application`.
- API suite 316 passed (+1 skipped: official set needs EXAMIN_DIR); new `test_errors.py`, `test_search_contract.py`,
  `tests/unit/test_tag_handlers.py` (handlers against in-memory ports, no database).
- Live: `POST /api/tags/search {filters:{name:{operator:"+",value:"sở"}},limit:3}` → `{data,total,page,limit}`;
  `sort:[{field:"nope"}]` → 422 `{code:"bad_sort", message, details:{fields, requestId}}`, same id in `X-Request-Id`.
- Live Tags page: list via `POST /tags/search`; "Thêm tag" → dialog closes, table shows 20 rows without a reload key;
  delete → 19 rows. Bank page pickers load tags through the same query hook.
- Web 149 tests, tsc and eslint (boundary rules) clean.

## UOW-02 topics, taxonomy and the academic context (2026-09-22)
- API modules `taxonomy` (subjects, semesters, topics tree) and `academic` (school years + terms + rollover, classes +
  members, structure, student record); `lint-imports` 4 contracts kept with `app.modules.academic` added;
  `test_architecture.py` green (identity columns read through lightweight tables, no module imports the old models).
- Endpoints moved to search (old GET lists answer 405): `GET /school-years` → `POST /school-years/search`,
  `GET /classes` → `POST /classes/search` (+ `school_year_id`, `grade_id`), `GET /school-levels` → `POST /school-levels/search`,
  `GET /grades` → `POST /grades/search` (+ `school_level_id`). Unchanged paths and JSON: `/taxonomy`, `/topics` (tree) and
  its create/rename/move/merge/delete, `/structure`, `/school-years/{id}` + activate/close/reopen + rollover preview/commit,
  class CRUD + members, `/students/{id}/record`. 34 routes now served by handlers (7 taxonomy, 27 academic).
- API suite 325 passed (+1 skipped: official set needs EXAMIN_DIR): new `tests/unit/test_topic_handlers.py` and
  `tests/unit/test_academic_handlers.py` (in-memory ports), `tests/test_academic_search.py` (typed filters, bad_sort /
  bad_filter, limit 1000, old GETs gone); demo script covered over HTTP by `test_topics_api.py` (add, rename, move, merge,
  delete), `test_school_years.py` + `test_rollover.py` (create, terms, activate, rollover), `test_classes_api.py` (members).
- Web: Topics, Structure, School years, Rollover, Classes, Class detail and Student record run on services → query hooks →
  page hooks → page components (routes one line); the header year lives in `stores/common/year.store.ts`
  (`examind.year.<org>`), `useYear()` kept. Users, exam and report screens read classes through `useClassOptionsQuery`.
  Web 152 tests, tsc and eslint clean. Not re-run on the live stack (running containers still on the previous image).

## UOW-03 identity: sessions, users, organisations (2026-09-22)
- API module `identity` (4 layers): sessions (login with lockout and IP throttle, refresh rotation with replay revocation, logout,
  switch-org, change password, `/auth/me`, `/me/orgs`), users of the org (CRUD, reset password, link/unlink, CSV/XLSX import),
  organisations and memberships (platform admin). Argon2 hashing, JWT and refresh-token secrets, the rate limiter and the spreadsheet
  reader are adapters behind ports; the class directory (academic application API) and the org seeder are wired by `main.py`.
  `schema/identity.py` now holds the only Table objects of `organizations`, `users`, `organization_members`, `refresh_tokens`;
  `app/models/{user,org}.py`, `app/deps.py`, `services/{auth,membership,users}.py`, `core/{security,passwords}.py` are re-export shims.
  The actor resolver is `identity.interface.deps.actor_from_request`; `OrgScope`/`org_scope`/`current_user`/`require_role` wrap it.
  `lint-imports` 4 contracts kept with `app.modules.identity` added; `test_architecture.py` green.
- Endpoints moved to search (old GET lists answer 405/404): `GET /users` → `POST /users/search` (+ `class_id`),
  `GET /admin/orgs` → `POST /admin/orgs/search` (+ `include_deleted`), `GET /admin/users` → `POST /admin/users/search`,
  `GET /admin/orgs/{id}/members` → `POST /admin/orgs/{id}/members/search`,
  `GET /admin/users/{id}/memberships` → `POST /admin/users/{id}/memberships/search`. Every other identity path and JSON body unchanged
  (login error bodies identical apart from `requestId`, cookies and JWT unchanged).
- API suite 340 passed (+1 skipped: official set needs EXAMIN_DIR): new `tests/unit/test_identity_handlers.py` (15 handler tests on
  in-memory ports) and `tests/test_identity_search.py`; existing tests changed only for the new URLs/shapes.
- Web: shell (AppShell, AppSidebar, OrgSwitcher, UserMenu, YearSwitcher, SessionRecovery) in `components/layout/`; login, change password,
  users (+ class members table), import wizard, admin orgs/accounts/memberships on services → query hooks → page hooks → page components.
  Switching organisation calls the API, clears the query cache (`useSwitchOrgMutation`), `router.push` + `router.refresh` — no full reload.
  Web 153 tests, tsc and eslint clean.
- Live (`docker compose up -d --build api worker web`, http://localhost:8088, trungtama/admin): login 200 (org_admin, trungtama);
  wrong password 401 `invalid_credentials` with the same message; `/auth/me` 200; `POST /users/search` role=student → `{data,total,page,limit}`
  total 30; `GET /users` 405; `/me/orgs` 200; `POST /auth/switch-org` 200; `/auth/refresh` 204; `/login` page 200.
