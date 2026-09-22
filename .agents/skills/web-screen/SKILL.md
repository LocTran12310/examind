---
name: web-screen
description: Add or change a screen in the Next.js app — route, page component, page hook, query hooks, service, store and tests — following the project's layers.
---

# Add a screen

Copy a finished slice: `components/page-components/Tags/` with `hooks/page-hooks/tags/`,
`hooks/react-query/use-query-tag.ts` and `services/tag.service.ts` is the smallest one.

## Steps

1. **Shapes.** Entity in `interfaces/<name>.interface.ts`, request bodies in `dtos/<name>.dto.ts`, unions in
   `types/<name>.type.ts`, labels and options in `constants/<name>.constant.ts`.
2. **Service** — the only file that talks HTTP:
   ```ts
   export const tagService = {
     search: (body: SearchBody) => http<SearchPage<Tag>>("/tags/search", { body }),
     create: (body: CreateTagBody) => http<Tag>("/tags", { body }),
     update: (id: string, body: UpdateTagBody) => http<Tag>(`/tags/${id}`, { method: "PATCH", body }),
     remove: (id: string) => http<void>(`/tags/${id}`, { method: "DELETE" }),
   };
   ```
3. **Keys** in `constants/react-query-key.constant.ts`: `ALL` first, then the parameterised ones.
4. **Query hooks** in `hooks/react-query/use-query-<domain>.ts`: `useXSearchQuery` (via `useSearchQuery`),
   detail queries with `enabled: Boolean(id)`, mutations invalidating `X_KEYS.ALL` in `onSuccess`
   (plus every other key the write moves).
5. **Page hook** in `hooks/page-hooks/<page>/use-<page>.ts(x)`: columns, dialog state, submit handlers,
   `formErrors(mutation.error)` for field errors. No JSX beyond cell renderers.
6. **Page component** in `components/page-components/<Page>/<Page>Page.tsx`: layout only
   (`ListLayout`, `PageHeader`, `DataTable`, `FormDialog`). Sub-components live in their own folder beside it.
7. **Route**: `src/app/(app)/…/page.tsx` renders the page component. Nothing else.
8. **Store** only for UI state that must survive navigation (chosen subject, chosen year): `stores/common/*.store.ts`.

## Tests

`src/__tests__/<page>.test.tsx` with `renderWithQuery`, `mockFetch(route("POST", "/api/x/search", searchPage([...])))`.
Cover: the list renders, a filter reaches the body (`lastBody`), a mutation refetches (count the search calls),
and any rule the page enforces. Add a case for what would break if someone removed the invalidation.

## Before you call it done

```bash
cd apps/web && pnpm typecheck && NODE_OPTIONS=--max-old-space-size=6144 pnpm lint && pnpm test
```
For anything visual, rebuild (`docker compose up -d --build web`) and look at the page — sticky headers, dark mode,
narrow width. Say what you checked and what you did not.
