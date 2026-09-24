---
id: UOW-03
slug: trial-api
title: Chạy thử đề đã giao, không ghi một dòng nào
demoable: true
duration: 2d
depends_on: []
requirements: [US-03]
verifies: [AC-04, AC-05]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — Chạy thử đề đã giao, không ghi một dòng nào

## Demo script
1. GET /assignments/{id}/paper: đề không lộ đáp án
2. POST /assignments/{id}/trial: có điểm, và đếm attempt/answer_facts không đổi

## In scope
- paper endpoint
- in-memory grading

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-04, AC-05 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4

## Verification evidence
- [ ] `make verify f=.ai/features/2026092402-exam-runner-and-roles` green on local, the only required environment
- [ ] Evidence exists for every AC in `verifies`, at both viewports
- [ ] `08-evidence.md` regenerated and its commit sha matches HEAD
- [ ] Every screenshot read: each one shows the claim its step makes, on the page the step names
