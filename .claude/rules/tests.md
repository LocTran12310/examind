---
globs: apps/api/tests/**, apps/web/src/**/*.test.ts, apps/web/src/**/*.test.tsx
paths: apps/api/tests/**, apps/web/src/**/*.test.ts, apps/web/src/**/*.test.tsx
---

# Tests

- API: `tests/test_<area>_api.py` drives HTTP against a real Postgres; `tests/unit/` drives handlers with fake
  ports from `tests/unit/fakes.py` — no database, no HTTP. A new use case gets both.
- Web: `renderWithQuery` + `mockFetch` from `src/__tests__/helpers.tsx`; `searchPage(...)` builds a search answer,
  `lastBody(fetch, "/x/search")` reads the request body. `next/navigation` comes from `router-mock.ts`.
- Assert behaviour, not implementation: what the user or the caller gets. Keep the meaning of an existing
  assertion when a contract changes; never weaken a test to make it pass.
- A test that fails intermittently is a bug to fix (add the missing tie-break/wait), not to retry.
- Run: `./scripts/verify.sh apps/api/tests …` (API, in docker) or `cd apps/web && pnpm test`.
