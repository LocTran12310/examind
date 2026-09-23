---
id: UOW-03
slug: exam-weighting
title: The exam states its own weighting
demoable: true
duration: 2d
depends_on: []
requirements: [US-03]
verifies: [AC-06]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — The exam states its own weighting

## Demo script
1. Mở đề: điểm từng phần, tổng thô và quy về thang 10, sửa điểm từng câu ngay đó

## In scope
- weighting strip
- per-question points made findable

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-06 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
