---
id: UOW-01
slug: structure
title: Cấp học › Khối › Lớp › Học sinh
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02]
verifies: [AC-01, AC-02, AC-03, AC-04, AC-05, AC-06]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Cấp học › Khối › Lớp › Học sinh

## Demo script
1. Create org TrungtamC → Cơ cấu trường shows THCS (6–9) and THPT (10–12)
2. In trungtama: THPT › Khối 10 → add class 10A2 → select it → add/import students
3. Delete Khối 10 while it has classes → refused 'còn 2 lớp'
4. Class dialog on Lớp học shows grades grouped by level

## In scope
- Migration 0012 + seed
- structure service + API
- /org/structure page
- GradeSelect in class form

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-01, AC-02, AC-03, AC-04, AC-05, AC-06 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
