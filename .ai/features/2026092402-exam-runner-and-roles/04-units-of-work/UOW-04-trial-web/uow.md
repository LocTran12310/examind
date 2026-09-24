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
- [x] All of AC-04, AC-05 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence
- [x] `make verify f=.ai/features/2026092402-exam-runner-and-roles` green on local, the only required environment
- [x] Evidence exists for every AC in `verifies`, at both viewports
- [x] `08-evidence.md` regenerated and its commit sha matches HEAD
- [x] Every screenshot read: each one shows the claim its step makes, on the page the step names
