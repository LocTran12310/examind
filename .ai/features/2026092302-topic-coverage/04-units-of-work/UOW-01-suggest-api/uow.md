---
id: UOW-01
slug: suggest-api
title: Untagged questions are listable, suggestible and no longer silent
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02, US-03]
verifies: [AC-01, AC-02, AC-04, AC-05]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Untagged questions are listable, suggestible and no longer silent

## Demo script
1. POST /questions/search {has_topic:false} → 102 câu
2. POST /questions/suggest-topics → 3 gợi ý kèm điểm và nguồn cho mỗi câu
3. Tải lại một đề mà máy không phân loại được → câu vào hàng chờ duyệt, không auto_approved

## In scope
- has_topic filter
- suggest endpoint
- ingestion api + adapter
- needs_review rule
- per-document count

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-01, AC-02, AC-04, AC-05 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
