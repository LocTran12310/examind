---
id: UOW-03
slug: users-and-classes
title: Org admin imports users and manages classes
demoable: true
duration: 2d
depends_on: [UOW-02]
requirements: [US-05]
verifies: [AC-15, AC-16, AC-17, AC-18, AC-19, AC-20]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — Org admin imports users and manages classes

## Demo script
1. Log in as trungtama/admin, open /org/users, create a teacher, edit, deactivate
2. Open /org/users/import, upload samples/students-30.csv → preview shows 30 valid rows
3. Upload samples/students-bad.csv → rows with errors are listed, nothing created
4. Commit the good file → download temp passwords CSV
5. Log in as one imported student → forced password change
6. Open /org/classes → class 10A1 lists its imported students; remove one
7. Reset a student's password from the users page → new temp password shown once

## In scope
- User CRUD + reset API
- CSV/XLSX import preview/commit
- Classes API
- Users, import and classes UI

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-15, AC-16, AC-17, AC-18, AC-19, AC-20 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
