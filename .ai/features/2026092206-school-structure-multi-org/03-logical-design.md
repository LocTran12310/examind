---
feature: school-structure-multi-org
adr_count: 4
---

# Logical design — School structure and users in several organisations

## Approach
**Structure.** New `school_levels`; `grades.school_level_id`; `classes.grade_id` (migration 0012
with backfill). `services/structure.py` owns levels/grades CRUD with range and dependency checks
and a `tree()` query with counts. `seed_org` adds THCS/THPT and attaches grades. The class service
accepts `grade_id` (and derives the integer `grade`). Web: `/org/structure` = tree + contextual
DataTable; `GradeSelect` groups grades by level.

**Membership.** New `organization_members` (PK user+org, role, is_active) and `users.last_org_id`
(migration 0013, backfill one home membership per user). `deps` builds `OrgScope(org_id, user,
role, is_super)` from the token's `org_id`, re-checking the membership (or super admin) and the
org's `can_login` on every request. `services/membership.py`: `role_in`, `orgs_for`, `switch`,
`link`, `unlink`. Services that looked at `User.organization_id/role` to validate other users now
join `organization_members` for the scope org. Auth issues tokens for the active org.

## Alternatives rejected
| Option | Why not |
| --- | --- |
| Global accounts (username unique system-wide) | Breaks org-code login and every existing username |
| Duplicate user rows per org | Two passwords, split history; exactly what the user wants to avoid |
| Keep role on users only | A person can be teacher in A and student in B |
| Level as an enum instead of a table | Loc Tran: levels are editable per org |

## Domain model
| Entity | Fields | Notes |
| --- | --- | --- |
| `SchoolLevel` | organization_id, code, name, grade_from, grade_to, sort | unique (org, code) |
| `Grade` (+) | school_level_id | level must contain `level` |
| `SchoolClass` (+) | grade_id | `grade` int kept as cache |
| `OrganizationMember` | user_id, organization_id, role, is_active, created_at | PK (user, org) |
| `User` (+) | last_org_id | home org = organization_id |

## Contracts
| Method & path | Role | Notes |
| --- | --- | --- |
| `GET /structure` | staff | levels › grades › classes with counts |
| `GET/POST /school-levels`, `PATCH/DELETE /school-levels/{id}` | org_admin (read: staff) | Page on GET |
| `GET/POST /grades`, `PATCH/DELETE /grades/{id}` | org_admin (read: staff) | `school_level_id` filter |
| `GET /classes?grade_id=` · `POST/PATCH /classes` `{grade_id}` | staff | |
| `GET /me/orgs` | any | orgs the user can switch to |
| `POST /auth/switch-org` `{org_id}` | any | new cookies, `MeOut` |
| `POST /users/link` `{org_code, username, role}` | org_admin | adds membership |
| `DELETE /users/{id}/membership` | org_admin | not the home org |

## State ownership
| State | Owner | Lifetime |
| --- | --- | --- |
| Active org | access token `org_id` + `users.last_org_id` | per session / persistent |
| Role per org | `organization_members` | persistent |

## Error taxonomy
| Condition | Code | HTTP | UI |
| --- | --- | --- | --- |
| Grade outside level range | `validation_error` | 422 | field error |
| Level/grade still in use | `in_use` | 409 | toast with count |
| No membership for org | `forbidden` | 403 | selector hides it |
| Token for a removed/suspended membership | `unauthenticated` | 401 | refresh → home org |
| Link: account not found | `not_found` | 404 | field error |
| Link: already a member | `conflict` | 409 | field error |

## Observability
Audit: `org.switch`, `member.link`, `member.unlink`, `level.*`, `grade.*` with actor and org.

## ADRs

### ADR-01 — Levels and grades are org-owned rows
**Context:** Levels must be seeded yet editable per org.
**Decision:** `school_levels` table with a grade range; grades hang off a level; classes point to a grade.
**Consequences:** Tree queries are plain joins; the integer grade stays for filters.
**Status:** accepted

### ADR-02 — Home org + memberships
**Context:** One login, several orgs, org-code login kept.
**Decision:** `users.organization_id` = home org (login namespace); `organization_members` = rights per org.
**Consequences:** Every "users of this org" query joins memberships.
**Status:** accepted

### ADR-03 — The token carries the active org; every request re-checks membership
**Context:** Switching must be instant, and revoking must take effect before the token expires.
**Decision:** `org_id` in the access token; `deps` verifies an active membership (or super admin) and org status on each request; `last_org_id` drives refresh and login.
**Consequences:** One extra indexed lookup per request.
**Status:** accepted

### ADR-04 — Super admin works inside orgs as org_admin
**Context:** Super admin needs to operate an org without owning a membership there.
**Decision:** `OrgScope.is_super` + role `org_admin` in non-system orgs; system org keeps `super_admin`.
**Consequences:** All org screens work unchanged for the super admin; audit shows the real actor.
**Status:** accepted
