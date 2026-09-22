# Demo evidence — ui-shadcn-shell

## UOW-01 — shadcn foundation, theme and shell (2026-09-22, live stack, in-app browser)
- /login renders on shadcn Card/Input with the theme button; with the OS in dark mode the page is dark on first load.
- After sign-in (trungtama/admin) every page has the navy sidebar (groups + icons, collapsible), header breadcrumb, organisation selector, theme button and avatar menu at the top right.
- Tests: `shell.test.tsx` (role menus, header, collapse), `theme.test.tsx` (switch + persistence), `login.test.tsx`.

## UOW-02 — Server-side DataTable (2026-09-22, live stack, in-app browser)
- /org/users: typed "dang" in the Họ tên filter → after the debounce the URL became `?full_name=dang` and the table showed the 4 "Đặng …" students (accent-insensitive, server-side).
- Light mode at 1400 px: navy toolbar bar, filter row under the headers, "Hiển thị 1–4 trên 4 kết quả" footer — the target back-office layout.
- Perf (dev Postgres, 369 360 users in a throwaway org, `users.list_users`, warm; data deleted afterwards):

| Query | Total | Time |
| --- | --- | --- |
| default page 1 (sort full_name) | 369 360 | 15.7 ms |
| full_name=bui | 52 766 | 31.2 ms |
| q=dung, sort -username | 52 766 | 101.9 ms |
| page 18 468 (last) | 369 360 | 211.5 ms |

  Before the `(organization_id, full_name, id)` index (migration 0011) the last page took 1 104 ms.
- Tests: `data-table.test.tsx` (debounce → URL → request, link restores state, paging, sort cycle, selection/confirm/reload, Back), `users/orgs/classes.test.tsx`, API `test_paging.py`.

## UOW-03 — All lists on the DataTable (2026-09-22, live stack)
- /org/review (dark mode): server-paged document list with counts, progress bars, reviewer select and "Duyệt N câu" links; "Của tôi" switch writes `?mine=true`.
- Documents, exams (row → "Chi tiết" panel with the exam's questions), AI models (toolbar Kiểm tra / Bật-Tắt / Phát hiện Ollama), tags (dialog CRUD) and the question bank (filters in the URL, bulk actions in the toolbar, shared pagination) — covered by `documents/exams/ai-models/tags/review-list/bank/bank-bulk.test.tsx`.
- API: every former bare list returns `Page` (`test_paging.py::test_former_bare_lists_are_paged`); 213 API tests pass.

## UOW-04 — Every other screen on shadcn, barrel removed (2026-09-22, live stack)
- Dark mode checked in the browser: review queue (answer highlight, hotkey legend, source page), reports ("Kết quả theo chuyên đề" tree with bars), student home and result view (score, per-part and per-topic bars, correct option highlighted).
- Found and fixed while checking: /org/reports and the exam page still read `/classes` as an array (crash "v.map is not a function") → both use the paged response now.
- Phone width (375 px): sidebar opens as a sheet from the header button; breadcrumb group hidden below `md`.
- `components/ui/` contains only shadcn CLI files (`ui-barrel.test.ts`); ESLint `no-restricted-imports` forbids `@/components/ui`; `tsc`, `eslint`, `next build` clean; 103 web tests pass.
