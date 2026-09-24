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
- [x] All of AC-04, AC-05 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence
- [x] `make verify f=.ai/features/2026092402-exam-runner-and-roles` green on local, the only required environment
- [x] Evidence exists for every AC in `verifies`, at both viewports
- [x] `08-evidence.md` regenerated and its commit sha matches HEAD
- [x] Every screenshot read: each one shows the claim its step makes, on the page the step names
