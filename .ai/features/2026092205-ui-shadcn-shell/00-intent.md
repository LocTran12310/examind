---
feature: ui-shadcn-shell
slug: 2026092205-ui-shadcn-shell
owner: Loc Tran
created: 2026-09-22
status: approved
---

# Intent — shadcn UI, app shell and server-side data tables

## Problem
The web app uses hand-written primitives (`components/ui/index.tsx`), has no dark mode, and each
list page renders its own `<table>`: only the question bank paginates, other lists load up to 200
rows and filter in the page. Teachers and centers expect the dense back-office screens they already use:
a left menu, a header with the organisation and user on the right, and tables with a search row
under the column headers and pagination.

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Org admin / teacher | Lists stop at 200 rows; filters differ per page | Every list: column search row, server paging, selection + toolbar actions, link keeps filters |
| Student | Separate top-bar layout | Same shell, left menu with student items |
| Everyone | Light only | Light / dark / system theme |
| Developer (Loc Tran) | Custom component API | Components are exactly shadcn's; follow shadcn docs |

## Success signal
All list screens use one DataTable whose filtering, sorting and paging happen on the server and
live in the URL; `components/ui/` contains only shadcn-generated files; every page renders in light
and dark mode; users list with 369k rows (perf fixture) pages in < 300 ms per request.

## Out of scope
- School levels, multi-org membership and the org switcher behaviour (F7 `school-structure-multi-org`)
- Changing business flows of review, exam taking, reports
- Export to Excel (toolbar "Xuất" stays CSV where it already exists)

## Constraints
| Kind | Detail |
| --- | --- |
| Components | shadcn/ui (new-york, Tailwind v4 CSS variables); files in `components/ui/` are never hand-edited |
| State | Table state = URL search params; no client-side filtering of loaded rows |
| Cost | Free/open-source packages only |

## Existing surface touched
- Replaced: `components/ui/index.tsx`, `app/(app)/AppShell.tsx`, every list page and form
- Reused: `lib/hooks.ts` (`useApi`), `lib/api.ts`, `lib/nav.ts`, `schemas/common.py` `Page`
- API: list endpoints return `Page` and accept `q`, `sort`, `page`, `page_size` + column filters
