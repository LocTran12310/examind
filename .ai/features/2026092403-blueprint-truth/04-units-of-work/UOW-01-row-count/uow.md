---
id: UOW-01
slug: row-count
title: Con số của một dòng ma trận là con số lệnh tạo đề sẽ dùng
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02]
verifies: [AC-01, AC-02, AC-03]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Con số của một dòng ma trận là con số lệnh tạo đề sẽ dùng

## Demo script
1. Dòng trên chuyên đề Mệnh đề, chọn Trắc nghiệm: số đọc 7 chứ không phải 14
2. Đổi sang Đúng/Sai: số đổi theo, không cần tạo đề mới biết
3. Đòi 10 câu khi chỉ có 7: màn hình nói chuyên đề có 14, hợp dòng này 7

## In scope
- per-row count
- shortfall explains

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
- [x] `make verify f=.ai/features/2026092403-blueprint-truth` green on local, the only required environment
- [x] Evidence exists for every AC in `verifies`, at both viewports
- [x] `08-evidence.md` regenerated and its commit sha matches HEAD
- [x] Every screenshot read: each one shows the claim its step makes, on the page the step names
