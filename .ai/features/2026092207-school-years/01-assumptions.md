---
feature: school-years
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | A school year belongs to an org: code "YYYY-YYYY", start/end dates, status planning / active / closed; exactly one active year per org | high | yes | Everything year-scoped | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-02 | Terms are fixed: HK1 and HK2 per year with their own dates (defaults 05/09–15/01 and 16/01–31/05) | high | no | Term filters | confirmed | Confirmed by Loc Tran in chat (2026-09-22): "Hk1 & HK2" |
| A-03 | A class belongs to one school year; a student may be in several classes of the same year and in several orgs | high | yes | Enrollment model | confirmed | Confirmed by Loc Tran in chat (2026-09-22): "Cho phép nhiều lớp. nhiều org." |
| A-04 | Closed years stay editable by org admins; every change to a closed year (and close/reopen itself) is written to the audit history, which is visible on the year, class and student | high | yes | Governance | confirmed | Confirmed by Loc Tran in chat (2026-09-22): "Có cho sửa, ghi vào history" |
| A-05 | Enrollment status per class member: đang học / lên lớp / ở lại / chuyển đi / tốt nghiệp, with joined/left dates | medium | no | Record page | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-06 | Each answer fact snapshots school_year_id, term (hk1/hk2 by date) and the ids of the student's classes in that year; class reports use the snapshot, not current membership | high | yes | Reports correctness | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-07 | Rollover: target class name = source name with its leading grade number +1 (10A1 → 11A1); grade 12 (the org's highest grade) → tốt nghiệp; per student the admin can pick lên lớp / ở lại (same-name class in the new year) / chuyển đi / tốt nghiệp; the source year can be closed at the end | medium | yes | Year change | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-08 | The header year selector is per browser and per org (localStorage), defaulting to the active year; year-scoped screens: Lớp học, Cơ cấu trường, Báo cáo, Giao bài lists | medium | no | Navigation | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-09 | Question bank, exams and accounts are not year-scoped | high | no | Scope | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-10 | "Đợt kiểm tra" = semester (hk1/hk2) × kind: Giữa kỳ 1, Cuối kỳ 1, Giữa kỳ 2, Cuối kỳ 2, plus Khảo sát / Thi thử / Ôn tập / Khác with a term; stored in the existing semester_code + exam_kind columns | high | no | Tagging | confirmed | Confirmed by Loc Tran in chat (2026-09-22): "Tài liệu sẽ phân theo Kỳ1 /Kỳ2, giữa kỳ 1, giữa kỳ 2, ..." |
| A-11 | Org ↔ user assignment from both screens is a super-admin feature: org list → members panel; new "Tài khoản" (all accounts) list → organisations panel; org admins keep "Thêm tài khoản có sẵn" in their org | medium | yes | Admin UI | confirmed | Confirmed by Loc Tran in chat (2026-09-22): "Org <-> Người dùng. Có thể gán được ở 2 màn hình qua lại" — who may do it assumed |
