---
feature: school-years
stories: 6
acceptance_criteria: 16
---

# Requirements — School years, student history, org ↔ user assignment

## US-01 — School years and terms

As an org admin I want school years with HK1/HK2 and one active year.

**Priority:** must

**AC-01** — CRUD and one active year
```gherkin
Given an org
When I create 2027-2028 and set it active
Then it gets HK1 and HK2 with default dates, the previous active year becomes closed or planning as chosen, and only one year is active
```

**AC-02** — Backfill
```gherkin
Given classes with a school_year string before the migration
When the migration runs
Then each distinct year exists as a school year, every class points at its year and the current year is active
```

**AC-03** — Year in the header
```gherkin
Given several years
When I choose a year in the header
Then Lớp học, Cơ cấu trường, Báo cáo and the assignment lists show that year only, and the choice survives reload
```

## US-02 — Closed years stay editable with history

**Priority:** must

**AC-04** — Edits audited
```gherkin
Given a closed year
When an org admin edits a class, its members or the year itself, or closes/reopens it
Then the change is saved and appears in the "Lịch sử" panel with who, when, what
```

## US-03 — Enrollment and answers remember the year

**Priority:** must

**AC-05** — Snapshot on answers
```gherkin
Given a student in 10A1 and 10-Toán-nâng-cao in 2026-2027
When she answers a question
Then the answer fact stores that year, the term by date and both class ids
```

**AC-06** — Reports by class and year
```gherkin
Given the student moved to 11A1 the next year
When I open the 10A1 report for 2026-2027 or the 11A1 report
Then her lớp-10 answers count only under 10A1 and her lớp-11 answers only under 11A1
```

**AC-07** — Term filter
```gherkin
Given answers in HK1 and HK2
When I filter a report by HK1
Then only HK1 answers count
```

## US-04 — Student record 10 → 12

**Priority:** must

**AC-08** — Timeline
```gherkin
Given a student with classes in several years
When I open "Hồ sơ học sinh"
Then I see each year with its classes and status, and results per year overall and per top-level topic
```

## US-05 — Year rollover

**Priority:** must

**AC-09** — Proposal
```gherkin
Given the active year 2026-2027 with 10A1, 11B, 12C
When I start "Chuyển năm học" to 2027-2028
Then the proposal maps 10A1 → 11A1, 11B → 12B, 12C → tốt nghiệp, every student defaulting to lên lớp / tốt nghiệp
```

**AC-10** — Exceptions and commit
```gherkin
Given I mark one student ở lại and one chuyển đi
When I confirm
Then target classes are created in 2027-2028, students are enrolled accordingly (ở lại → 10A1 of the new year), source memberships get their statuses, and optionally the old year is closed and the new one activated
```

**AC-11** — Safe to repeat
```gherkin
Given a rollover was already committed for a class
When I run it again
Then existing target classes and memberships are reused, nothing is duplicated
```

## US-06 — Đợt kiểm tra and org ↔ user assignment

**Priority:** must

**AC-12** — One picker
```gherkin
Given the upload form and the bank filters
When I pick "Giữa kỳ 1"
Then semester hk1 and kind Giữa kỳ are set/filtered, and lists show "Giữa kỳ 1"
```

**AC-13** — Org → users
```gherkin
Given the super admin on the organisation list
When they select an org
Then a members panel lists its members with role and home org, and they can add an account (org code + username + role), change the role, lock or remove a non-home membership
```

**AC-14** — User → orgs
```gherkin
Given the super admin on "Tài khoản" (all accounts)
When they select an account
Then a panel lists its organisations with role, and they can add an org with a role, change the role or remove it (not the home org)
```

**AC-15** — Same data both ways
```gherkin
Given a membership added from either screen
When I open the other screen
Then it is there with the same role
```

**AC-16** — History
```gherkin
Given membership, year or class changes
When I open "Lịch sử" on the org, account, year or class
Then I see the audit entries for it, newest first, paged on the server
```
