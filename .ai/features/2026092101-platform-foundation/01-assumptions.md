---
feature: platform-foundation
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | Org code is 3–32 chars of `[a-z0-9-]`, stored lower-case, matched case-insensitively (`TrungtamA` == `trungtama`) | high | yes | Login contract, org create form | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-21) — to confirm at final review |
| A-02 | Username unique per org, case-insensitive, `[a-z0-9._-]` 3–64 chars; auto-generated from full name without diacritics when CSV leaves it blank (`nguyenvana`, then `nguyenvana2`) | medium | yes | CSV import, login | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-21) — to confirm at final review |
| A-03 | Roles are exactly `super_admin`, `org_admin`, `teacher`, `student`; one role per user | high | yes | RBAC everywhere | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-21) — to confirm at final review |
| A-04 | super_admin lives in a reserved org `system` that cannot be edited, suspended or deleted | high | no | Org CRUD edge cases | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-21) — to confirm at final review |
| A-05 | Teachers may create students and reset student passwords, but not manage other teachers or admins | medium | no | User management permissions | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-21) — to confirm at final review |
| A-06 | Access token 15 min, refresh token 30 days, both httpOnly SameSite=Lax cookies; refresh tokens stored hashed and revoked on org suspend / password reset | high | yes | Auth contract | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-21) — to confirm at final review |
| A-07 | Lockout: 5 failed logins for the same (org, username) within 15 min → locked 15 min; per-IP limit 30/min | medium | no | Login UX | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-21) — to confirm at final review |
| A-08 | CSV columns: `full_name` (required), `username`, `role` (default student), `class`; UTF-8 with or without BOM; `.xlsx` also accepted; max 2000 rows | medium | no | Import screen | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-21) — to confirm at final review |
| A-09 | Temp passwords are 10 chars from an unambiguous alphabet, returned once in a downloadable CSV and never retrievable again | high | no | Import UX | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-21) — to confirm at final review |
| A-10 | Topic tree is per organisation, seeded from a shared Toán 10–12 (GDPT 2018) template at org creation; nodes carry `level_kind` ∈ strand/topic/subtopic/type; max depth 5 | medium | yes | Topic model, stats roll-up in later features | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-21) — to confirm at final review |
| A-11 | Subjects, grades (6–12) and semesters (HK1/HK2) are fixed seed data per org in this feature; editing them is out of scope | medium | no | Taxonomy screens | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-21) — to confirm at final review |
| A-12 | Tags are per org with a group ∈ method/skill/source/custom; name unique per (org, group) | high | no | Tag screens | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-21) — to confirm at final review |
| A-13 | Deleting a topic node with children or (later) questions is refused; merging moves children + references to the target | medium | no | Topic editing | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-21) — to confirm at final review |
| A-14 | UI language is Vietnamese only for MVP | high | no | Copy | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-21) — to confirm at final review |
| A-15 | Org soft delete sets `deleted_at`, frees nothing, blocks login; hard delete allowed only when the org has no users other than its admins | medium | no | Org CRUD | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-21) — to confirm at final review |
| A-16 | Seed super admin credentials come from env `SUPERADMIN_USERNAME`/`SUPERADMIN_PASSWORD` (dev default `admin` / `admin12345`) and must be changed on first login | high | no | Bootstrap | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-21) — to confirm at final review |
