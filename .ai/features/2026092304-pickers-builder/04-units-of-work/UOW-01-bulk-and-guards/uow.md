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
- [ ] All of AC-03, AC-05, AC-06 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
