---
feature: platform-foundation
stories: 7
acceptance_criteria: 24
---

# Requirements — Platform foundation

## US-01 — Run the whole stack locally

As a developer, I want one command to start every service so that the product runs the same on my Mac and on the VM.

**Priority:** must

**AC-01** — Stack starts
```gherkin
Given a clean checkout with .env copied from .env.example
When I run docker compose up -d
Then postgres, minio, api, web and caddy become healthy
And GET /api/health returns 200 with {"status":"ok","db":"ok","storage":"ok"}
```

**AC-02** — Migrations and seed
```gherkin
Given the database is empty
When the api container starts
Then Alembic migrations run to head
And the system org and the super admin from env exist exactly once, even after restarts
```

## US-02 — Log in with organisation code

As any user, I want to log in with my center code, username and password so that the same username can exist in different centers.

**Priority:** must

**AC-03** — Happy path
```gherkin
Given an active org "trungtama" with user "hs01" and password "Secret123!"
When I submit org "TrungtamA", username "HS01", password "Secret123!"
Then I am redirected to my role's home page
And access and refresh cookies are set httpOnly
```

**AC-04** — Generic failure
```gherkin
Given any of: unknown org, unknown user, wrong password, inactive user
When I submit the login form
Then I see "Sai tổ chức, tên đăng nhập hoặc mật khẩu"
And the response is identical for every case (status 401, same body)
```

**AC-05** — Suspended or deleted org
```gherkin
Given org "trungtama" is suspended or soft-deleted
When a user of that org logs in with correct credentials
Then login is refused with "Tổ chức đang bị khóa"
And any existing refresh tokens of that org no longer refresh
```

**AC-06** — Lockout
```gherkin
Given 5 failed attempts for (trungtama, hs01) within 15 minutes
When a 6th attempt is made, even with the right password
Then it is refused with status 429 until 15 minutes have passed
```

**AC-07** — Remember org code
```gherkin
Given I logged in successfully with org "TrungtamA" before on this browser
When I open /login again
Then the org field is prefilled with "TrungtamA"
```

**AC-08** — Session refresh and logout
```gherkin
Given my access token expired and my refresh token is valid
When the web app calls the API
Then it refreshes transparently and the call succeeds
And after I log out the refresh token is revoked
```

## US-03 — Forced password change

As a user with a temporary password, I must set my own password before using the app.

**Priority:** must

**AC-09** — Forced change
```gherkin
Given my account has must_change_password = true
When I log in
Then every page except /change-password redirects there
And after I set a new password (≥ 8 chars, not equal to the old one) I reach my home page
```

## US-04 — Super admin manages organisations

As the platform operator, I want to create, edit, suspend and delete centers.

**Priority:** must

**AC-10** — Create org with first admin
```gherkin
Given I am super_admin
When I create org code "TrungtamA", name "Trung tâm A", admin username "admin"
Then the org exists with code "trungtama" and the seeded topic tree, subjects, grades, semesters
And I am shown the admin's temporary password once
```

**AC-11** — Duplicate or invalid code
```gherkin
Given org "trungtama" exists
When I create another org with code "TRUNGTAMA" or "trung tam!"
Then I see a field error and nothing is created
```

**AC-12** — List and edit
```gherkin
Given several orgs exist
When I open /admin/orgs
Then I see code, name, status, user count and created date, searchable by code or name
And I can edit name and code (with a warning that users must use the new code)
```

**AC-13** — Suspend / reactivate / delete
```gherkin
Given org "trungtama" is active
When I suspend it, then reactivate it
Then logins are refused while suspended and allowed after reactivation
When I delete it
Then it is soft-deleted and hidden from the default list
And the system org has no suspend or delete action
```

**AC-14** — Only super_admin
```gherkin
Given I am org_admin, teacher or student
When I call any /api/admin/orgs endpoint
Then I get 403
```

## US-05 — Org admin manages users and classes

As a center admin, I want to create accounts in bulk and group students into classes.

**Priority:** must

**AC-15** — Create, edit, deactivate a user
```gherkin
Given I am org_admin of "trungtama"
When I create a teacher, edit their full name, then deactivate them
Then the list reflects each change and the deactivated teacher cannot log in
```

**AC-16** — CSV import
```gherkin
Given a CSV with 30 rows of full_name and class, some usernames blank
When I import it
Then 30 students are created with unique usernames, assigned to their classes (created if missing)
And I can download a CSV of username + temporary password exactly once
```

**AC-17** — CSV errors
```gherkin
Given a CSV where row 7 has no full_name and row 9 duplicates an existing username
When I preview the import
Then rows 7 and 9 are reported with reasons and nothing is created until I fix or skip them
```

**AC-18** — Reset password
```gherkin
Given a student forgot their password
When a teacher or org_admin resets it
Then a new temporary password is shown once, must_change_password is set, and old refresh tokens are revoked
```

**AC-19** — Tenant isolation
```gherkin
Given users exist in orgs A and B
When an org_admin of A lists, reads or edits users or classes
Then they only ever see A's data, and requesting a B id returns 404
```

**AC-20** — Classes
```gherkin
Given I am org_admin or teacher
When I create class "10A1" (grade 10, school year 2026-2027) and add or remove students
Then the class shows its members and a student can belong to several classes
```

## US-06 — Topic tree and tags

As a teacher, I want one editable knowledge tree and tags so that questions and stats can be grouped at any level.

**Priority:** must

**AC-21** — Browse and edit the tree
```gherkin
Given my org was seeded with the Toán 10–12 tree
When I open /org/topics
Then I can expand "Giải tích › Nguyên hàm" and add child "Nguyên hàm từng phần"
And I can rename, move (drag or "move to") and delete leaf nodes; paths update for the whole subtree
```

**AC-22** — Merge and guard
```gherkin
Given node X has children
When I delete X
Then it is refused with a message
When I merge X into Y
Then X's children move under Y and X disappears
```

**AC-23** — Tags
```gherkin
Given I am teacher or org_admin
When I create tag "đổi biến" in group method, rename it, and delete it
Then the tag list per group reflects each change and duplicates in the same group are refused
```

## US-07 — Render a question fully

As any user, I want every question shown with stem, options, answer, solution and images so that nothing in the source is lost.

**Priority:** must

**AC-24** — QuestionView
```gherkin
Given a question with LaTeX in the stem, an image in option C and a multi-step solution with an image
When it is rendered in mode "review"
Then math renders with KaTeX, images appear in their fields, answer and solution are visible
When it is rendered in mode "exam"
Then answer and solution are hidden
And empty parts render no empty box
```

## Non-functional

| Kind | Requirement | Verified by |
| --- | --- | --- |
| Security | Passwords hashed with argon2id; no password or token ever logged | T-01-04 |
| Portability | Images build for linux/arm64 and linux/amd64 | T-01-01 |
| Performance | Login p95 < 300 ms locally (argon2 cost tuned) | T-01-04 |
