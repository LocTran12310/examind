---
feature: school-structure-multi-org
stories: 4
acceptance_criteria: 13
---

# Requirements — School structure and users in several organisations

## US-01 — School levels and grades

As an org admin I want Cấp học › Khối as editable entities.

**Priority:** must

**AC-01** — Seeded on create
```gherkin
Given a super admin creates an organisation
When it is created
Then it has levels THCS (khối 6–9) and THPT (khối 10–12) with grades 6…12 attached
```

**AC-02** — CRUD with guards
```gherkin
Given levels and grades exist
When an org admin adds, renames or deletes a level or grade
Then grade numbers must fit the level's range and be unique, and deleting a level with grades or a grade with classes is refused with the count
```

**AC-03** — Backfill
```gherkin
Given data from before the migration
When the migration runs
Then every existing grade is attached to the level whose range contains it and every class with a grade number gets the matching grade_id
```

## US-02 — Structure page

As an org admin I want to manage Cấp học › Khối › Lớp › Học sinh in one place.

**Priority:** must

**AC-04** — Tree with counts
```gherkin
Given the org's structure
When I open "Cơ cấu trường"
Then a tree shows levels, grades and classes with class and student counts
```

**AC-05** — Contextual table
```gherkin
Given I select a node in the tree
When it is a level, a grade or a class
Then the right side shows the level's grades, the grade's classes or the class's students in a server-paged table with add/edit/delete
```

**AC-06** — Class form uses the structure
```gherkin
Given I create or edit a class anywhere
When I pick its grade
Then the grades are grouped by level and the class stores grade_id and grade
```

## US-03 — Membership and switching

As a user of several organisations I want to pick the organisation I work in.

**Priority:** must

**AC-07** — Header selector
```gherkin
Given I belong to several organisations (or I am super admin)
When I open the organisation selector in the header
Then I see those organisations (all of them for super admin) and choosing one reloads the app inside it
```

**AC-08** — Scope enforced
```gherkin
Given I switched to organisation B
When I call any API
Then results come only from B, with my role in B, and a token for an org where my membership was removed or disabled is rejected
```

**AC-09** — Login lands on the last org
```gherkin
Given I switched to B before logging out
When I log in again with my home org code
Then the app opens in B if my membership is still active, else in my home org
```

**AC-10** — Suspended org
```gherkin
Given organisation B is suspended
When I open the selector or refresh my session
Then B is not offered and I am put back in my home organisation
```

## US-04 — Accounts from other organisations

As an org admin I want to add an existing account from another organisation.

**Priority:** must

**AC-11** — Link an account
```gherkin
Given a teacher account exists in organisation B
When an org admin of A adds it by B's code and the username with a role
Then the user appears in A's user list with that role and a "Từ B" badge, and can switch to A
```

**AC-12** — Unlink
```gherkin
Given a linked member of A
When the org admin removes the membership
Then the account still exists in B, loses access to A, and its A class memberships are removed; the home membership cannot be removed
```

**AC-13** — Per-org roles in checks
```gherkin
Given a user is a teacher in A and a student in B
When A assigns reviewers or B assigns exams to students
Then each check uses the role in that organisation
```
