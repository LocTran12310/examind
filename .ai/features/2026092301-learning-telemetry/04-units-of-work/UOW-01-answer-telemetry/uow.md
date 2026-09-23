---
id: UOW-01
slug: answer-telemetry
title: Answers carry timing, attempt number and no fact when unanswered
demoable: true
duration: 2d
depends_on: []
requirements: [US-01]
verifies: [AC-01, AC-02]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Answers carry timing, attempt number and no fact when unanswered

## Demo script
1. Làm một bài, quay lại một câu, nộp → answer_facts có seconds_spent và first_attempt
2. Mở bài luyện rồi bỏ dở → hết giờ tự nộp, mastery không đổi

## In scope
- timing columns
- runner reports seconds
- grading skips unanswered
- migration

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-01, AC-02 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
