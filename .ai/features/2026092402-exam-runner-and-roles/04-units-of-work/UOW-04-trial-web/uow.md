---
id: UOW-04
slug: trial-web
title: Giáo viên ngồi vào ghế học sinh
demoable: true
duration: 2d
depends_on: []
requirements: [US-03]
verifies: [AC-04, AC-05]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-04 — Giáo viên ngồi vào ghế học sinh

## Demo script
1. Từ đề đã giao, chọn Làm thử, trả lời, nộp, thấy điểm và đáp án

## In scope
- entry point
- runner in trial mode
- result

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
