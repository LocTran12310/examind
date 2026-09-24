---
id: UOW-04
slug: review-ui
title: Thấy và sửa được mức độ ngay chỗ đang duyệt
demoable: true
duration: 2d
depends_on: []
requirements: [US-04]
verifies: [AC-06]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-04 — Thấy và sửa được mức độ ngay chỗ đang duyệt

## Demo script
1. Thẻ duyệt hiện mức độ và nói rõ máy gán hay người đặt, sửa ngay tại đó

## In scope
- difficulty on the review card
- provenance shown
- edit in place

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-06 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4

## Verification evidence
- [ ] `make verify f=.ai/features/2026092404-difficulty-at-upload` green on local, the only required environment
- [ ] Evidence exists for every AC in `verifies`, at both viewports
- [ ] `08-evidence.md` regenerated and its commit sha matches HEAD
- [ ] Every screenshot read: each one shows the claim its step makes, on the page the step names
