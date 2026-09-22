---
feature: school-structure-multi-org
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | A school level (Cấp học) is an org-owned entity: code, name, grade range, sort; new orgs get THCS 6–9 and THPT 10–12; Tiểu học is not seeded | high | yes | Seed, structure page | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-02 | A grade (Khối) belongs to exactly one level; its grade number must lie in the level's range and is unique per org | high | yes | Data model | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-03 | A class belongs to one grade (`grade_id`); the old integer `classes.grade` stays as a cache so bank/exam filters keep working | high | no | Migration | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-04 | Deleting a level with grades, or a grade with classes, is refused (409 with the count); classes are deleted from the class list as today | high | no | UX | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-05 | `users.organization_id` is the home org (where the username lives and the user logs in); `organization_members` holds (user, org, role, is_active) and is the source of permissions per org | high | yes | Auth everywhere | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-06 | Roles are per org; `users.role` mirrors the home membership so existing code keeps a meaning | medium | no | Consistency | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-07 | After login the last used org opens (`users.last_org_id`) if its membership is still active and the org can log in; otherwise the home org | high | no | Login UX | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-08 | Switching org re-issues the access token; the refresh token follows `last_org_id` | high | no | Sessions | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-09 | Super admin sees every org in the selector and works inside it with org_admin rights; audit records the super admin as actor | medium | no | Admin power | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-10 | An org admin (or super admin) of the target org adds an existing account by home org code + username and a role; removing a membership never deletes the account; the home membership cannot be removed | medium | yes | Privacy | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-11 | A suspended target org disappears from the selector; if it was active, the next request falls back to the home org | medium | no | Suspension | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-12 | The org detail "Thành viên" tab from the chat plan is replaced by "Vào tổ chức" (switch) + the normal Users page | medium | no | Admin UI | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
