---
id: UOW-04
slug: bank-review
title: Question bank and review
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02, US-03]
verifies: [AC-01, AC-02, AC-04, AC-05, AC-06]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-04 — Question bank and review

## Demo script
1. Ngân hàng câu: môn, bộ lọc, chip, facets
2. Duyệt câu: hàng đợi, sửa, đáp án

## In scope
- question aggregate
- bank search/facets read model
- review, triage, answer key

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-02, AC-04, AC-05, AC-06 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
