---
id: UOW-03
slug: subject-scoped-reports
title: Báo cáo còn đọc được khi có nhiều môn
demoable: true
duration: 2d
depends_on: []
requirements: [US-03]
verifies: [AC-05, AC-06]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — Báo cáo còn đọc được khi có nhiều môn

## Demo script
1. Báo cáo mặc định vẫn là mọi môn, chọn được một môn
2. Ở mọi môn, các mạch kiến thức nhóm dưới môn của chúng

## In scope
- subject picker on reports
- grouping by subject in the topic tree

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-05, AC-06 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
