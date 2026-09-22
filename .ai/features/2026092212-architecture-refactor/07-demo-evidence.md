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

## UOW-04 question bank and review (2026-09-22)
- API module `bank` (4 layers): the Question aggregate (dataclass on `shared/infrastructure/schema/bank.py`, the only Table objects of
  `questions`, `question_topics`, `question_tags`, `review_events`) with create, update, delete (in-use guard, duplicates released), bulk,
  review actions (approve / reject / restore / skip, spot_ok / spot_fail, threshold feedback), answer key, approve-confident, reviewer
  assignment, key audit and ingestion triage (near-duplicates) through handlers. Quality rules, search text, answer-key parsing, review
  and key-audit rules are pure domain services. Topic / tag / subject checks go through the new `taxonomy/application/api.py`
  (`TaxonomyApi`), the reviewer check through `IdentityApi.role_in` + new `is_super`; both are wired in `main.py`
  (`register_taxonomy`, `register_staff_directory`). Source documents, org threshold and submitted answers are read through Core adapters.
  `lint-imports` 4 contracts kept with `app.modules.bank` added; `test_architecture.py` green.
- Old layout kept working through shims: `app/models/{question,review}.py` and `QuestionTopic`/`QuestionTag` in `models/document.py`
  re-export the bank dataclasses; `services/{bank,triage,key_audit,answer_key,question_quality,search_text}.py` delegate
  (`bank.search_ids`, `IN_USE_CHECKS`, `release_duplicates_of`, `triage_hook`, `audit`); `schemas/questions.py` and the question part of
  `schemas/documents.py` re-export the bank schemas; `routers/documents.parsed_many` uses the bank presenter. `routers/{questions,review}.py`,
  `services/review.py`, `schemas/review.py` removed. `strip_markup` / `PART_RE` / `ROMAN` moved to `shared/domain/text.py` (ingestion re-imports).
- Endpoints moved to search (old GETs answer 405): `GET /questions` → `POST /questions/search` (bank params at the top of the body,
  `topic_ids` / `tag_ids` arrays, `limit` ≤ 1000; typed filters stem, created_at, updated_at, number, grade), `GET /questions/facets` →
  `POST /questions/facets` (same body), `GET /review/documents` → `POST /review/documents/search` (+ `mine`),
  `GET /review/flagged` → `POST /review/flagged/search`. Every other question / review path and JSON body unchanged.
- API suite 351 passed (+1 skipped: official set needs EXAMIN_DIR); official golden set with EXAMIN_DIR 1 passed. New
  `tests/unit/test_bank_handlers.py` (11 handler tests on in-memory ports); existing tests changed only for the new URLs/shapes.
  `test_triage.py::test_pdf_copy_of_docx_is_marked_duplicate` failed once on a re-run (two original questions with the same text tie on
  similarity; the duplicate query is unchanged from before) and passed on the next run.
- Web: bank list (SubjectTabs, FilterSheet, FilterChips, facets, BulkBar), question detail / new, review list and review document (queue,
  editor, answer key, approve-confident) on `question.service` / `review.service` → `use-query-question` / `use-query-review` → page hooks →
  page components; routes one line. Subject per org in `stores/common/bank-subject.store.ts` (same `examind.bank.subject.<org>` key).
  QuestionView, Markdown, MarkdownEditor, TopicPicker, QuestionForm, QuestionFields moved to `components/common/`. Exam builder search box
  and the dev preview use the query hooks (lint exception line). Web 154 tests, tsc and eslint clean.
- Live (`docker compose up -d --build api worker web`, http://localhost:8088, trungtama/admin): `POST /questions/search {status:"all"}` total
  397 (396 from the 18 documents + the demo question), usable 377; `POST /review/documents/search` 18 documents, 396 questions;
  Toán 356 → + one topic subtree 43 → + a source tag 2 (e.g. "Hoán vị, chỉnh hợp, tổ hợp", tag of Trường THPT Thuận Thành); facets for the three filters types {mcq 1, short_answer 1};
  queue of a document 1, flagged 0; `GET /questions` 405.
