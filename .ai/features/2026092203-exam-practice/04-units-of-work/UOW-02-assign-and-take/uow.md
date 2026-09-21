---
id: UOW-02
slug: assign-and-take
title: Students take assigned exams with a timer and autosave
demoable: true
duration: 2d
depends_on: [UOW-01]
requirements: [US-02, US-03, US-04, US-06]
verifies: [AC-05, AC-06, AC-07, AC-08, AC-09, AC-10, AC-11, AC-15, AC-20]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Students take assigned exams with a timer and autosave

## Demo script
1. Assign 'Kiểm tra 15 phút' to 10A1: now → +1 day, 15 minutes, shuffle on, results after submit
2. Log in as a 10A1 student → /home shows it under 'Đang mở'
3. Start → countdown, navigator, answers hidden; answer 5 questions, reload → answers and time restored
4. Switch tab and back → counted
5. Submit → score out of 10 appears immediately
6. Start an assignment whose window closed → refused

## In scope
- Assignments API + student home API
- Attempts: start, answers, submit, expiry, grading, facts
- Assign dialog + student home
- Exam page

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-05, AC-06, AC-07, AC-08, AC-09, AC-10, AC-11, AC-15, AC-20 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
