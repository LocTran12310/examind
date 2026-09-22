# Demo evidence — school-years

Live stack, in-app browser, 2026-09-22 (migrations 0014 + 0015 applied to the dev DB).

## UOW-01 — Years, HK1/HK2, header selector, history
- Backfill: trungtama and ttb got 2026-2027 (Đang học) with HK1 05/09–15/01 and HK2 16/01–31/05; trungtama's 3 classes point at it.
- Header shows "2026-2027 · Đang học"; Năm học page lists dates, terms, status and class count.
- API tests: create/activate (previous active closed)/close/reopen, term dates inside the year, classes filtered by year, closed-year class edit saved and audited with `closed_year` (`test_school_years.py`, `test_audit_api.py`); web: selector per org + class list scoped (`school-years.test.tsx`).

## UOW-02 — Answers remember year/term/classes; reports; record
- Backfill: all 30 existing answer facts got a year and class ids.
- API: a student in 10A1 + "Toán nâng cao 10" → facts carry both classes; after moving to 11A1 next year her answers count under 10A1 only; term filter works (`test_year_history.py`).
- Hồ sơ · Bùi Văn Châu: 2027-2028 (11A1, no work yet) and 2026-2027 (10A1 · Lên lớp, 30 câu, HK1 7 %, Hình học 8 %, Đại số 6 %).

## UOW-03 — Chuyển năm học
- Năm học → 2026-2027 → Chuyển năm học: proposal 10A1 → 11A1, 10A2 → 11A2, 10A3 → 11A3; 30 lên lớp by default.
- Set Đặng Thanh Quân to "Ở lại lớp (10A1)", untick activation, confirm → "29 lên lớp, 1 ở lại … Tạo lớp: 11A1, 10A1, 11A2".
- API: exceptions, graduation of the top grade, activation closing the old year, idempotent re-run (`test_rollover.py`).

## UOW-04 — Đợt kiểm tra, org ↔ user both ways
- Upload and bank use one "Đợt kiểm tra" picker (Giữa kỳ 1 … Cuối kỳ 2, others with a term); lists show "Giữa kỳ 1" (`exam-period.test.ts`, `documents/bank.test.tsx`).
- Super admin → Tài khoản → filter "lạn" → Cô Nguyễn Thị Lan → organisations panel: Trung tâm B (Tổ chức gốc), Trung tâm A — the membership added earlier from the Users page of A.
- Org → members panel on Tổ chức; add by org code + username, change role, lock, remove (not the home org); history per org/account (`test_admin_memberships.py`, `admin-members.test.tsx`).

## Totals
API 246 passed · web 120 passed · tsc, eslint, next build clean.
