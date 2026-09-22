---
id: UOW-02
slug: history
title: Answers remember year, term and classes; reports by year/term; student record
demoable: true
duration: 2d
depends_on: [UOW-01]
requirements: [US-03, US-04]
verifies: [AC-05, AC-06, AC-07, AC-08]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Answers remember year, term and classes; reports by year/term; student record

## Demo script
1. Student in 10A1 submits → her fact has 2026-2027, hk1, [10A1]
2. Reports: pick 2026-2027 and HK1 → numbers change accordingly
3. Người dùng → student → Hồ sơ: years, classes, results per topic

## In scope
- Migration 0015 facts snapshot + class_members status
- Stats filters
- Record API + page

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-05, AC-06, AC-07, AC-08 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
