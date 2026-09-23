---
id: UOW-01
slug: history
title: A history worth restoring: a wider snapshot and a batch id
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02]
verifies: [AC-01, AC-03, AC-05]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — A history worth restoring: a wider snapshot and a batch id

## Demo script
1. Đổi mức độ cho 3 câu → review_events có 3 dòng cùng một batch_id
2. Mỗi dòng ghi đủ môn, lớp, mức độ, chuyên đề và tag trước/sau
3. POST /question-events/search trả một dòng cho cả lượt sửa, kèm lý do nếu không hoàn tác được

## In scope
- snapshot widening
- batch_id migration
- events search

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-01, AC-03, AC-05 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4

## Verification evidence
- [ ] `make verify f=.ai/features/2026092305-bulk-safety` green on local, the only required environment
- [ ] Evidence exists for every AC in `verifies`, at both viewports
- [ ] `08-evidence.md` regenerated and its commit sha matches HEAD
- [ ] Every screenshot read: each one shows the claim its step makes, on the page the step names
