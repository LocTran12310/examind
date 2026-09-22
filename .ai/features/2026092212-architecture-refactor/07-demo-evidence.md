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
