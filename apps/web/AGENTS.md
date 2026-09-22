# apps/web — working agreement

Next.js 15 App Router, React 19, Tailwind v4, shadcn/ui, TanStack Query + Table, zustand, vitest.
Package manager: pnpm. Read [`.ai/architecture.md`](../../.ai/architecture.md) first; the root
[`AGENTS.md`](../../AGENTS.md) holds the rules shared with the API.

## Layout

```
src/app/                                  routes only — page.tsx renders one page component; (app)/layout.tsx checks the session
src/components/ui/                        shadcn CLI output, never edited by hand
src/components/common/<Name>/<Name>.tsx   shared composites (DataTable/, FormDialog, FormField, DatePicker, QuestionView, …)
src/components/layout/<Name>/<Name>.tsx   Providers, AppShell, sidebar, switchers, theme
src/components/page-components/<Page>/    <Page>Page.tsx and its own sub-components
src/hooks/common/                         use-table-query (URL state), use-me, use-year, …
src/hooks/react-query/use-query-<domain>.ts   useXxxQuery / useXxxSearchQuery / useXxxMutation
src/hooks/page-hooks/<page>/use-<page>-*.ts(x)  one page's state: columns, dialogs, submit
src/services/<module>.service.ts          `export const xService = {…}` — the only callers of lib/common/http
src/stores/                               zustand: UI state only, never server data
src/constants/ dtos/ interfaces/ types/   *.constant.ts · *.dto.ts · *.interface.ts · *.type.ts
src/lib/common/                           http, query-client, search-body, form-errors, datetime, session, nav, …
src/lib/page-libs/<page>/                 pure helpers of one page
```

## Rules (ESLint + `src/__tests__/architecture.test.ts`)

- Only `services/**` import `http`; only `hooks/react-query/**` import `@tanstack/react-query`
  (plus `lib/common/query-client`, `components/layout/Providers`, tests).
- `app/**` imports neither services nor query hooks. A route file is a few lines.
- `components/**` and `hooks/page-hooks/**` never call `fetch`.
- `components/common/**` never imports a page component.
- The removed layout stays removed: no `@/lib/hooks`, `@/lib/api`, `@/lib/types`, `@/components/app/*`,
  `@/components/data-table/*`, no `useApi`.
- shadcn components are imported one file each. No raw `<select>`, no native date inputs — use `OptionSelect`,
  `DatePicker` / `DateTimePicker`. `components/ui` is CLI output: regenerate, do not hand-edit.
- Named exports only; no barrel files. Hooks and services are kebab-case files, component folders PascalCase.
- Vietnamese UI copy; keep existing wording unless the task changes it.

## Data flow

Table state lives in the URL (`useTableQuery`) → `toSearchBody(params, kinds, resourceParams)` → the resource's
`useXxxSearchQuery(body)` → `xService.search(body)` → `POST /api/x/search`. `DataTable` takes `useRows` (the
search hook), `params` (resource parameters) and optional `refetchWhile` for polling. Column filters declare their
kind in `meta.filter` (`text | select | number | date`, `param: true` for a resource parameter).

React Query owns server state: one QueryClient (staleTime 0, retry 1, no refetch on focus), lists keep the previous
page while the next loads, mutations invalidate `<ENTITY>_KEYS.ALL` (and whatever else they move), switching
organisation clears the cache. Field errors come from `formErrors(mutation.error)` (`details.fields`).

## Checks

```bash
cd apps/web
pnpm typecheck                                         # tsc --noEmit
NODE_OPTIONS=--max-old-space-size=6144 pnpm lint       # eslint (the heap flag avoids an OOM on the full tree)
pnpm test                                              # vitest
pnpm build                                             # next build
```

Test helpers: `src/__tests__/helpers.tsx` (`mockFetch`, `route`, `searchPage`, `lastBody`, `lastQuery`,
`renderWithQuery`) and `router-mock.ts` for `next/navigation`. Render page components with `renderWithQuery`.

## Adding a screen (short form — the `web-screen` skill has the long one)

1. `interfaces/` + `dtos/` for the shapes, `constants/react-query-key.constant.ts` for `<ENTITY>_KEYS`.
2. `services/<module>.service.ts` — one object, one method per endpoint.
3. `hooks/react-query/use-query-<domain>.ts` — query and mutation hooks, invalidation in `onSuccess`.
4. `hooks/page-hooks/<page>/` — columns, dialog state, submit handlers.
5. `components/page-components/<Page>/<Page>Page.tsx` — layout and composition only.
6. `src/app/**/page.tsx` — render the page component.
7. A test in `src/__tests__/<page>.test.tsx` using `renderWithQuery` and `mockFetch`.
