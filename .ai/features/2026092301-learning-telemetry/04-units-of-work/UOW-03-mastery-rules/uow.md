---
id: UOW-03
slug: mastery-rules
title: One weak-topic rule, decay, recompute and a weekly snapshot
demoable: true
duration: 2d
depends_on: []
requirements: [US-03, US-04]
verifies: [AC-05, AC-06, AC-07]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — One weak-topic rule, decay, recompute and a weekly snapshot

## Demo script
1. Chuyên đề 2 lượt trả lời → 'chưa đủ dữ liệu', không vào kế hoạch ôn
2. Rebuild dựng lại đúng số cũ; bảng tuần có dữ liệu sau backfill

## In scope
- weak_topics()
- decay
- rebuild endpoint
- student_topic_week
- weekly job
- backfill

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-05, AC-06, AC-07 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
