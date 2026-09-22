---
id: UOW-01
slug: years
title: School years with HK1/HK2, header year selector, year-scoped classes
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02]
verifies: [AC-01, AC-02, AC-03, AC-04, AC-16]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — School years with HK1/HK2, header year selector, year-scoped classes

## Demo script
1. Năm học: 2026-2027 (đang học) created by backfill with HK1/HK2 dates
2. Create 2027-2028 → header selector lists both → pick 2027-2028 → Lớp học and Cơ cấu trường are empty
3. Close 2026-2027, edit a class name in it → 'Lịch sử' shows the change flagged năm đã khóa

## In scope
- Migration 0014 years/terms/class link
- Year service + API + audit read API
- YearSwitcher, Năm học page, HistoryPanel
- Classes/structure filtered by year

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-01, AC-02, AC-03, AC-04, AC-16 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
