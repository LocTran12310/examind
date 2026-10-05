# School structure and users in several organisations

## Problem
A center's data is flat: a class carries a bare grade number, there is no notion of THCS/THPT, and
nothing groups khối → lớp → học sinh. Every account belongs to exactly one organisation, so a
teacher who works at two centers needs two accounts, and the super admin can only manage
organisations from the outside — never work inside one.

## Outcome
---
feature: school-structure-multi-org
slug: 2026092206-school-structure-multi-org
owner: Loc Tran
created: 2026-09-22
status: approved
---

## Success signal
An org admin builds "THPT › Khối 10 › 10A2" and imports its students without leaving the structure
page; a teacher added from another org switches org from the header and sees only that org's data;
no request made with one org selected returns another org's rows.

## Out of scope
- Several campuses/branches under one org (the header selector switches organisations)
- Shared login identity across orgs by email/SSO (login stays org code + username)
- Moving question banks between organisations

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Org admin | Types a grade number per class | Opens "Cơ cấu trường": Cấp học › Khối › Lớp › Học sinh, adds/edits each level |
| New organisation | Starts with grades 6–12 only | Starts with THCS (6–9) and THPT (10–12) seeded, editable |
| Teacher at two centers | Two usernames, two logins | One login; picks the center in the header selector |
| Super admin | CRUD organisations only | Selects any organisation in the header and works inside it |

## Constraints
| Kind | Detail |
| --- | --- |
| Security | Membership is checked on every request, not only at switch time |
| Compatibility | Existing classes, grades and users keep working after the migration (backfill) |
| UI | Built with the F6 shadcn components and DataTable |

## Existing surface touched
- Reused: `grades`, `classes`, `class_members`, user import, DataTable, OrgSwitcher, `OrgScope`
- New: `school_levels`, `organization_members`, `users.last_org_id`, `/org/structure`, `/auth/switch-org`, `/me/orgs`
