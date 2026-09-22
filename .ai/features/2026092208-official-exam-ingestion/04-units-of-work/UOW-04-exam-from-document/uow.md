---
id: UOW-04
slug: exam-from-document
title: Tạo đề từ tài liệu
demoable: true
duration: 2d
depends_on: [UOW-02]
requirements: [US-05]
verifies: [AC-11, AC-12]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-04 — Tạo đề từ tài liệu

## Demo script
1. Approve a document's questions → 'Tạo đề từ tài liệu' → exam with 12/4/6 in order, 10 điểm
2. A rejected question is skipped and reported

## In scope
- POST /documents/{id}/exam
- Button on the document

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-11, AC-12 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
