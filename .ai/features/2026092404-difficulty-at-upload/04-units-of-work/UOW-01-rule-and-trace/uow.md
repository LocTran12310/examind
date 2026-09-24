---
id: UOW-01
slug: rule-and-trace
title: Quy tắc vị trí và dấu vết mức độ
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02]
verifies: [AC-02, AC-04]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Quy tắc vị trí và dấu vết mức độ

## Demo script
1. Câu Phần I số 1 ra nb, Phần III ra vd — thuần, không cần model
2. Người đặt mức độ thì dấu vết là manual; lệnh máy không đổi được nó

## In scope
- difficulty_source column
- position rule
- manual is untouchable

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-02, AC-04 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
