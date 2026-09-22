---
id: UOW-03
slug: order-shadcn
title: Exam order draft, shadcn consistency, preview dialog
demoable: true
duration: 2d
depends_on: []
requirements: [US-04, US-05]
verifies: [AC-04, AC-05, AC-06]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — Exam order draft, shadcn consistency, preview dialog

## Demo script
1. Sắp xếp thứ tự → swap → Lưu thứ tự (1 request)
2. Preview maximised fills the dialog

## In scope
- ExamQuestions
- raw tags → shadcn
- preview body

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-04, AC-05, AC-06 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
