---
id: UOW-02
slug: undo
title: Hoàn tác: a bulk edit restored as one unit
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02]
verifies: [AC-01, AC-02, AC-04, AC-05]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Hoàn tác: a bulk edit restored as one unit

## Demo script
1. POST /questions/bulk/undo với batch vừa sửa → các câu trở lại đúng như cũ
2. Một câu đã bị xóa → từ chối cả lượt, nêu tên câu
3. Hoàn tác lần hai → 409, lượt hoàn tác cũng nằm trong lịch sử

## In scope
- undo command
- guards on restore
- undo recorded as an event

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-02, AC-04, AC-05 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence
- [x] `make verify f=.ai/features/2026092305-bulk-safety` green on local, the only required environment
- [x] Evidence exists for every AC in `verifies`, at both viewports
- [x] `08-evidence.md` regenerated and its commit sha matches HEAD
- [x] Every screenshot read: each one shows the claim its step makes, on the page the step names
