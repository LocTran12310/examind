# Demo evidence — school-structure-multi-org

Live stack, in-app browser, 2026-09-22 (migrations 0012 + 0013 applied to the dev DB).

## UOW-01 — Cấp học › Khối › Lớp › Học sinh
- Migration backfill on the dev DB: trungtama got THCS (khối 6–9, 4 grades) and THPT (10–12, 3 grades); classes 10A1/10A2 point at Khối 10 › THPT.
- API: new org `ttb` created by the super admin → THCS/THPT seeded (`test_structure.py::test_new_org_gets_thcs_and_thpt_with_grades`).
- /org/structure (super admin working inside Trung tâm A): tree with class/student counts; Khối 10 → "Thêm lớp" (khối preselected) → 10A3 appears in the table and the tree (3 lớp).
- THPT → select Lớp 10 → Xóa → confirm → toast "Khối còn 3 lớp" (409 from the API).
- Class dialog everywhere uses the grade picker grouped by level; bank grade filter grouped by level; report class filter grouped by khối.

## UOW-02 — Active organisation, header selector
- system/admin → selector lists Examind (hệ thống), Trung tâm A, Trung tâm B → picks Trung tâm A → full reload inside A with org-admin menus plus "Hệ thống › Tổ chức".
- API tests: switch changes scope and role; no rows from the other org; login reopens the last org; disabled membership / suspended org → 401 then refresh falls back home; super admin sees every org (`test_membership.py`).

## UOW-03 — Accounts from other organisations
- In Trung tâm A → Người dùng → "Thêm tài khoản có sẵn" → ttb / gvlan / Giáo viên → toast "Đã thêm Cô Nguyễn Thị Lan"; the row shows the badge "Từ ttb".
- Logged in as ttb/gvlan: selector shows Trung tâm B (home) and Trung tâm A · Giáo viên → switched to A → Lớp học lists A's 10A1, 10A2, 10A3.
- API tests: A cannot rename or reset the password of B's account; role/lock in A only; unlink removes A's class memberships and access, home membership cannot be removed; per-org roles in class/assignment/review checks.

## Totals
API 229 passed · web 110 passed · tsc, eslint, next build clean.
