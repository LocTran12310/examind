---
id: UOW-02
slug: keyboard-review-queue
title: Teachers clear the review queue with single keys
demoable: true
duration: 2d
depends_on: [UOW-01]
requirements: [US-02, US-03, US-04]
verifies: [AC-04, AC-05, AC-06, AC-07, AC-08, AC-09, AC-11, AC-13]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Teachers clear the review queue with single keys

## Demo script
1. Open de-kho in /org/review → queue shows 'thiếu đáp án' group first, counter 1/5
2. Press 2 → answer B saved; Enter → approved and next question shown
3. Press E → edit the stem in Markdown with KaTeX preview → Ctrl+Enter saves
4. Press X on a bad question → rejected; K goes back
5. Open the PDF document's queue → source page image shown beside the question
6. 'Dán đáp án' with '1B 2B 3B 4B 5B' → summary 'Đã áp dụng 5'
7. 'Duyệt tất cả câu tin cậy cao' → auto-approved become approved

## In scope
- Queue + actions + edit API with events and spot-check loop
- Answer-key paste, approve-confident, PDF page images
- Queue page with keyboard map
- Inline editor + bulk dialogs + review-flow test

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-04, AC-05, AC-06, AC-07, AC-08, AC-09, AC-11, AC-13 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
