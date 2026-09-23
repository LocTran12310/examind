---
id: UOW-03
slug: bank-safety
title: The bank: undo in the toast, recent changes, and a count on every action
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02, US-03]
verifies: [AC-01, AC-03, AC-04, AC-05, AC-06]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — The bank: undo in the toast, recent changes, and a count on every action

## Demo script
1. Đặt Lớp 12 nhầm cho 2 câu → toast có Hoàn tác → hai câu trở lại như cũ
2. Thay đổi gần đây: ai, lúc nào, sửa gì, mấy câu — hoàn tác từng lượt
3. Mỗi nút bulk nói rõ sẽ đổi bao nhiêu câu

## In scope
- toast undo
- recent changes sheet
- counts on the bulk actions

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-03, AC-04, AC-05, AC-06 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence
- [x] `make verify f=.ai/features/2026092305-bulk-safety` green on local, the only required environment
- [x] Evidence exists for every AC in `verifies`, at both viewports
- [x] `08-evidence.md` regenerated and its commit sha matches HEAD
- [x] Every screenshot read: each one shows the claim its step makes, on the page the step names
