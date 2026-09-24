---
id: UOW-01
slug: runner
title: Khung làm bài đứng yên và xem được cả đề
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02]
verifies: [AC-01, AC-02, AC-03]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Khung làm bài đứng yên và xem được cả đề

## Demo script
1. Chuyển qua lại mười câu: khung không đổi bề rộng
2. Bật Toàn đề: cả đề hiện ra, trả lời ngay tại đó, bảng câu đánh dấu đã làm

## In scope
- width fix
- whole-paper mode

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-02, AC-03 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence
- [x] `make verify f=.ai/features/2026092402-exam-runner-and-roles` green on local, the only required environment
- [x] Evidence exists for every AC in `verifies`, at both viewports
- [x] `08-evidence.md` regenerated and its commit sha matches HEAD
- [x] Every screenshot read: each one shows the claim its step makes, on the page the step names
