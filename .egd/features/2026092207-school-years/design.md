---
feature: school-years
adr_count: 5
---

# Logical design — School years, student history, org ↔ user assignment

## Approach
**Years.** `school_years` (org, code, name, start/end, status) and `school_terms` (year, code hk1/hk2,
start/end); `classes.school_year_id` (string kept as cache). `services/school_years.py`: CRUD,
`activate` (one active per org), `close`/`reopen`, `year_for_date`, `term_for_date`. Header
`YearSwitcher` + `YearProvider` (localStorage per org) feed `school_year_id` to year-scoped lists.

**Enrollment + snapshot.** `class_members` gains `status`, `joined_at`, `left_at`. `answer_facts`
gains `school_year_id`, `term_code`, `class_ids uuid[]` filled at grading time from the student's
active memberships in classes of that year; stats filter classes by `:klass = ANY(class_ids)` and
by year/term. Backfill assigns years by date and classes by current membership in that year.

**Record.** `GET /students/{id}/record`: enrollments by year + per-year aggregates from facts.

**Rollover.** `services/rollover.py`: `preview(source, target_code)` builds the class mapping and
default actions; `commit(plan)` creates/reuses the target year and classes (idempotent by name+year),
enrolls students, marks source memberships, optionally closes/activates.

**Audit.** `GET /audit?target_type&target_id` (paged) + `HistoryPanel` component; services record
`closed_year=True` in the data when a change touches a closed year.

**Org ↔ user (super admin).** `membership.add/update/remove(db, actor, org_id, user_id, …)` replace
scope-bound helpers; `/admin/orgs/{id}/members` and `/admin/users` + `/admin/users/{id}/memberships`
share them; the org admin's `/users/link` calls the same functions.

**Đợt kiểm tra.** Web helper maps `{semester_code, exam_kind}` ⇄ label; upload + bank use one picker.

## Alternatives considered
| Option | Why not |
| --- | --- |
| Separate `enrollments` table beside class_members | Two sources of truth; class_members + status/dates is enough when a class belongs to a year |
| Filter class reports by current membership + date range | Wrong after students move classes; snapshot is exact and cheap |
| Global year selector in the URL | Every link would need to carry it; a per-org stored preference is simpler |
| Custom terms | Out of scope (Loc Tran: HK1 & HK2) |

## Domain model
| Entity | Fields | Notes |
| --- | --- | --- |
| `SchoolYear` | organization_id, code, name, start_date, end_date, status | unique (org, code); partial unique active |
| `SchoolTerm` | school_year_id, code (hk1/hk2), start_date, end_date | unique (year, code) |
| `SchoolClass` (+) | school_year_id | |
| `ClassMember` (+) | status, joined_at, left_at | |
| `AnswerFact` (+) | school_year_id, term_code, class_ids | GIN on class_ids |

## Contracts
| Method & path | Role | Notes |
| --- | --- | --- |
| `GET/POST /school-years`, `PATCH/DELETE /school-years/{id}` | read staff, write org_admin | Page |
| `POST /school-years/{id}/activate` · `/close` · `/reopen` | org_admin | audited |
| `POST /school-years/{id}/rollover/preview` `{target_code}` | org_admin | plan |
| `POST /school-years/{id}/rollover/commit` `{plan}` | org_admin | result counts |
| `GET /classes?school_year_id=` · `GET /structure?school_year_id=` | staff | |
| `GET /stats/*?school_year_id&term_code` | staff/student | |
| `GET /students/{id}/record` | staff | |
| `GET /audit?target_type&target_id` | org_admin (own org), super admin | Page |
| `GET/POST /admin/orgs/{id}/members`, `PATCH/DELETE /admin/orgs/{id}/members/{uid}` | super admin | |
| `GET /admin/users`, `GET/POST /admin/users/{id}/memberships`, `PATCH/DELETE /admin/users/{id}/memberships/{org}` | super admin | |

## State ownership
| State | Owner | Lifetime |
| --- | --- | --- |
| Chosen year | browser localStorage per org | per browser |
| Year of an answer | answer_facts snapshot | permanent |

## Failure modes
| Condition | Code | HTTP | UI |
| --- | --- | --- | --- |
| Second active year | handled by activate (old one closed) | — | — |
| Delete year with classes | `in_use` | 409 | toast |
| Year code/date invalid | `validation_error` | 422 | field |
| Rollover target class exists with other grade | `conflict` | 409 | row error |
| Remove home membership | `validation_error` | 422 | toast |

## Observability
Audit actions: `year.*`, `class.*` (with `closed_year`), `member.*`, `rollover.commit` (counts).

## ADRs

### ADR-01 — Classes belong to a school-year row
**Context:** Years must be real objects with terms and status.
**Decision:** `school_years` + `school_terms`; `classes.school_year_id`; string kept as cache.
**Consequences:** Rollover and year filters are joins; old code reading the string keeps working.
**Status:** accepted

### ADR-02 — Answer facts snapshot year, term and classes
**Context:** Students move; reports must not follow them.
**Decision:** Write `school_year_id`, `term_code`, `class_ids` when grading; filter on the snapshot.
**Consequences:** Exact historic reports; backfill is best-effort for old rows.
**Status:** accepted

### ADR-03 — Idempotent rollover by (year, class name)
**Context:** Year change must be repeatable and correctable.
**Decision:** Preview → commit; target classes found or created by name within the target year; memberships upserted.
**Consequences:** Re-running only fills gaps.
**Status:** accepted

### ADR-04 — One membership service for both admin screens
**Context:** Org → users and user → orgs must show the same data.
**Decision:** `membership.add/update/remove(actor, org_id, user_id)`; three routers call it.
**Consequences:** One set of rules (home membership cannot be removed).
**Status:** accepted

### ADR-05 — History is the audit log
**Context:** Closed years stay editable but must be traceable.
**Decision:** Read API over `audit_logs` filtered by target; services add `closed_year` to entries.
**Consequences:** No new table; history covers everything already audited.
**Status:** accepted
