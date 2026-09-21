---
id: UOW-02
slug: personal-review
title: Students and teachers get personalised review exams
demoable: true
duration: 2d
depends_on: [UOW-01]
requirements: [US-02, US-03]
verifies: [AC-04, AC-05, AC-06, AC-07]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Students and teachers get personalised review exams

## Demo script
1. Student presses 'Tạo đề ôn tập' → 20 questions, plan shows 'Chuyên đề yếu: …', runs in the exam page, results immediately
2. Mastery updates after submitting
3. Teacher on class 10A1 → 'Giao đề ôn cá nhân' (15 câu, 30 phút) → every student's home shows their own exam

## In scope
- Adaptive generator
- Practice + class assignment API
- Buttons and plan display

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-04, AC-05, AC-06, AC-07 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
