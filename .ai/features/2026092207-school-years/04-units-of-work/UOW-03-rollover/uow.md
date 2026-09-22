---
id: UOW-03
slug: rollover
title: Chuyển năm học wizard
demoable: true
duration: 2d
depends_on: [UOW-02]
requirements: [US-05]
verifies: [AC-09, AC-10, AC-11]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — Chuyển năm học wizard

## Demo script
1. Năm học 2026-2027 → Chuyển năm học → 2027-2028: 10A1→11A1, 10A2→11A2, 10A3→11A3
2. Mark one student ở lại, one chuyển đi → Xác nhận → 11A1 has the others, 10A1 (2027-2028) has the retained one
3. Run again → nothing duplicated

## In scope
- Rollover service + API
- Wizard page

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-09, AC-10, AC-11 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
