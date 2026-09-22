---
globs: apps/web/src/**
paths: apps/web/src/**
---

# Web layers

- Route (`src/app/**/page.tsx`) renders one page component and nothing else — no data, no services, no query hooks.
- Page component composes UI; page hook (`hooks/page-hooks/<page>/`) holds its state, columns and submit handlers.
- Query hooks (`hooks/react-query/use-query-<domain>.ts`) are the only users of `@tanstack/react-query`;
  services (`services/<module>.service.ts`) are the only callers of `lib/common/http`. `fetch` is banned in
  components and page hooks.
- Lists: URL state (`useTableQuery`) → `toSearchBody` → `useXxxSearchQuery(body)`; `DataTable` takes `useRows`,
  `params` and optional `refetchWhile`. Mutations invalidate `<ENTITY>_KEYS.ALL`.
- shadcn only: one import per component file, `OptionSelect` instead of `<select>`, `DatePicker` /
  `DateTimePicker` instead of native date inputs; `components/ui` is CLI output, never hand-edited.
- Named exports, no barrels. Keep Vietnamese UI copy.
- After editing: `cd apps/web && pnpm typecheck && NODE_OPTIONS=--max-old-space-size=6144 pnpm lint && pnpm test`.
