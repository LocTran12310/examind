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
