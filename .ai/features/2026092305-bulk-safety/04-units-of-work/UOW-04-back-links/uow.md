---
id: UOW-04
slug: back-links
title: A way back from every detail page
demoable: true
duration: 2d
depends_on: []
requirements: [US-04]
verifies: [AC-07]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-04 — A way back from every detail page

## Demo script
1. Báo cáo bài giao, kết quả bài làm, thêm câu hỏi, xem trước câu hỏi: đều có đường về danh sách

## In scope
- BackLink on the four pages that lack one

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-07 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence
- [x] `make verify f=.ai/features/2026092305-bulk-safety` green on local, the only required environment
- [x] Evidence exists for every AC in `verifies`, at both viewports
- [x] `08-evidence.md` regenerated and its commit sha matches HEAD
- [x] Every screenshot read: each one shows the claim its step makes, on the page the step names
