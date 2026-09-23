---
id: UOW-01
slug: bulk-and-guards
title: Bulk by suggestion, subject and grade, and a builder that refuses an empty topic
demoable: true
duration: 2d
depends_on: []
requirements: [US-02, US-03, US-04]
verifies: [AC-03, AC-05, AC-06]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Bulk by suggestion, subject and grade, and a builder that refuses an empty topic

## Demo script
1. POST /questions/bulk/topics với 20 cặp khác nhau → một request, báo số câu bỏ qua
2. POST /questions/bulk đặt môn và lớp cho các câu chưa phân môn
3. Ma trận đề có dòng chuyên đề rỗng → 422 nói rõ chuyên đề nào

## In scope
- bulk/topics
- subject and grade in bulk
- blueprint empty-topic guard

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-03, AC-05, AC-06 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence
- [x] `make verify f=.ai/features/2026092304-pickers-builder` green on local, the only required environment
- [x] Evidence exists for every AC in `verifies`, at both viewports (S5, S6, S8)
- [x] `08-evidence.md` regenerated and its commit sha matches HEAD
- [x] Every screenshot read: each one shows the claim its step makes, on the page the step names
