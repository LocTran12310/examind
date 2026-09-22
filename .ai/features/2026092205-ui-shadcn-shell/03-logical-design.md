---
feature: ui-shadcn-shell
adr_count: 6
---

# Logical design — shadcn UI, app shell and server-side data tables

## Approach
Initialise shadcn in `apps/web` (Tailwind v4, CSS variables) and generate the components we use.
App-level building blocks live in `components/app/` (PageHeader, FormField, ConfirmDialog,
ThemeToggle, OrgSwitcher, UserMenu, AppSidebar) and `components/data-table/` (DataTable on
TanStack Table in manual mode, column filter row, toolbar, pagination, `useTableQuery` hook that
reads/writes URL search params). Every list page declares columns + filter kinds and passes the
API path; the hook turns the URL into the request. On the API a shared `paging` helper applies
`q`, `sort` and `page/page_size` to a SQLAlchemy select and returns `Page`; each list endpoint
declares its sortable/filterable columns.

## Alternatives rejected
| Option | Why not |
| --- | --- |
| Adapter keeping the old component API | Rejected by Loc Tran: components must follow the shadcn docs directly |
| Client-side filtering on a big page | Breaks at 369k rows; state not shareable |
| AG Grid / MUI DataGrid | Heavier, not shadcn, licence limits on advanced features |

## Domain model
No new tables. `Page` envelope already exists in `apps/api/app/schemas/common.py`.

## Contracts
| Method & path | Change |
| --- | --- |
| `GET /admin/orgs`, `/users`, `/documents`, `/questions` | add `sort`; column filters (`code`, `name`, `status`…) |
| `GET /classes`, `/exams`, `/assignments`, `/tags`, `/ai-models`, `/review/documents`, `/review/flagged` | bare list → `Page`; `q`, `sort`, `page`, `page_size`, column filters |
| All paged lists | `page_size=all` returns up to 1000 rows for pickers |

## State ownership
| State | Owner | Lifetime |
| --- | --- | --- |
| Table filters, sort, page | URL search params | per link |
| Theme | next-themes (localStorage) | per browser |
| Sidebar collapsed | shadcn sidebar cookie | per browser |

## Error taxonomy
| Condition | Code | HTTP | UI |
| --- | --- | --- | --- |
| Unknown sort field | `bad_sort` | 422 | toast, falls back to default sort |
| Page beyond last | — | 200 with empty items | pagination jumps to last page |
| Network error while paging | — | — | inline error row with "Thử lại" |

## Observability
Request log already records path + query; slow list queries (> 300 ms) logged with params.

## ADRs

### ADR-01 — shadcn components verbatim
**Context:** Loc Tran wants to follow the shadcn docs without a custom layer.
**Decision:** `components/ui/` holds only CLI-generated files; app composites live elsewhere; ESLint forbids the old barrel import.
**Consequences:** Upgrades are `shadcn add --overwrite`; every page was rewritten once.
**Status:** accepted

### ADR-02 — URL is the table state
**Context:** Filters must survive reload and be shareable; data is too large for the browser.
**Decision:** `useTableQuery` reads/writes `useSearchParams`; the API does all filtering, sorting and paging.
**Consequences:** Back button walks through filter history (router.replace for typing, push for paging).
**Status:** accepted

### ADR-03 — One paging helper on the API
**Context:** Seven endpoints return bare lists; each paged one re-implements paging.
**Decision:** `app/services/paging.py` applies q / column filters / sort / page to a select from a declared column map and returns `Page`.
**Consequences:** Consistent params and errors; new lists get paging for free.
**Status:** accepted

### ADR-04 — TanStack Table in manual mode
**Context:** Need headless columns, selection, sorting UI that matches shadcn's data-table guide.
**Decision:** `@tanstack/react-table` with manualPagination/manualSorting/manualFiltering.
**Consequences:** Same pattern as the shadcn docs; no client-side row model for filtering.
**Status:** accepted

### ADR-05 — shadcn NativeSelect in dense forms, Radix Select in tables and filters
**Context:** 14 native `<select>`s in editors/forms (answer key per option, blueprint rows, upload metadata); Radix Select needs a sentinel for empty values and is heavier per row.
**Decision:** Forms with many inline selects use shadcn `NativeSelect` (a shadcn component, styled with the theme); table filters, toolbars and single-choice form fields use Radix `Select` through `components/app/OptionSelect`.
**Consequences:** Both follow the shadcn docs; keyboard/mobile behaviour of native selects is kept where rows repeat.
**Status:** accepted

### ADR-06 — TanStack Table pinned to v8
**Context:** `pnpm add @tanstack/react-table` installed v9, whose API (`getCoreRowModel` removed) no longer matches the shadcn data-table guide.
**Decision:** Pin `@tanstack/react-table@^8` until the shadcn guide moves to v9.
**Consequences:** One deliberate upgrade later; DataTable is the only consumer.
**Status:** accepted
