---
id: UOW-03
slug: knn-learning
title: Approved questions teach topic suggestions
demoable: true
duration: 2d
depends_on: [UOW-01]
requirements: [US-04]
verifies: [AC-12]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — Approved questions teach topic suggestions

## Demo script
1. Approve Câu 2 of de-kho with topic 'Lũy thừa với số mũ thực'
2. Upload a new file with a near-identical question → its suggested topic is 'Lũy thừa với số mũ thực' (source knn)

## In scope
- kNN suggestion via trigram similarity to approved questions

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-12 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
