---
name: api-search
description: Add or change a list resource behind the search contract (POST /<resource>/search, typed filters, sort, paging, facets) and wire the web table to it.
---

# Add a searchable list

The contract (architecture ADR-03): `POST /api/<resource>/search` with
`{page, limit, q?, sort?: [{field, desc}], filters?: {<field>: {operator?, value?, from?, to?}}, …resource params}`
answering `{data, total, page, limit}`.

## API side

1. **Columns.** In the module's `infrastructure/read_models.py`:
   ```python
   TAG_COLS = {"group": Col(tags.c.group, "exact"), "name": Col(tags.c.name), "subject_id": Col(tags.c.subject_id, "uuid", sortable=False)}
   ```
   Kinds: `text` (`* = + - !`), `number` / `date` (timestamp) / `day` (date column) (`= < <= > >=`, `from`/`to`),
   `exact` / `uuid` / `bool` (a list means "any of"). Unknown field or operator answers 422 `bad_filter`.
2. **Reader.** Build the base `select(...)` scoped by `org_id`, apply resource parameters yourself, then
   `search(session, stmt, req, COLS, text=[...], default_sort=[...], scalars=False)` and map rows to DTOs.
   Return `Page(rows, total, req.page, req.limit)`.
3. **Query handler** takes `SearchRequest` plus the resource parameters; the router body subclasses `SearchBody`:
   ```python
   class TagSearchBody(SearchBody):
       subject_id: str | None = None
       include_shared: bool = True
   ```
   and the route returns `PageOut[TagOut]`.
4. **Facets** (optional) take the same body and count per dimension, each facet excluding its own filter.

## Web side

1. `services/<module>.service.ts`: `search: (body: SearchBody) => http<SearchPage<T>>("/x/search", { body })`.
2. `constants/react-query-key.constant.ts`: `X_KEYS.SEARCH(body)` under `X_KEYS.ALL`.
3. `hooks/react-query/use-query-<domain>.ts`: `useXSearchQuery(body, options)` via `useSearchQuery`.
4. Table columns declare `meta.filter` (`text | select | number | date`; `param: true` sends the value as a
   resource parameter instead of a filter). `DataTable` gets `useRows={useXSearchQuery}` and `params`.

## Tests

- `tests/test_<area>_search.py`: each operator, a range, sort, paging, 422 for a bad field/operator/sort.
- Web: `lastBody(fetch, "/x/search")` shows what the URL produced.
