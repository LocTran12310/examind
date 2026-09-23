---
id: UOW-02
slug: pickers
title: Pickers that start on the suggestion and count questions
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02]
verifies: [AC-01, AC-02, AC-03, AC-04, AC-05]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Pickers that start on the suggestion and count questions

## Demo script
1. Nhấn T: cây mở sẵn ở chuyên đề được gợi ý, chưa áp dụng gì
2. Số bên cạnh chuyên đề là số câu hỏi; chuyên đề rỗng hiện 0
3. Chọn 20 câu → Gán theo gợi ý → còn lại giảm, câu không có gợi ý được nêu tên

## In scope
- initial topic
- counts from facets
- gán theo gợi ý
- scrollable paged filter

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-02, AC-03, AC-04, AC-05 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence
- [x] `make verify f=.ai/features/2026092304-pickers-builder` green on local, the only required environment
- [x] Evidence exists for every AC in `verifies`, at both viewports (S2, S3, S6, S7, S8)
- [x] `08-evidence.md` regenerated and its commit sha matches HEAD
- [x] Every screenshot read: each one shows the claim its step makes, on the page the step names
