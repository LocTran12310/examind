---
id: UOW-01
slug: attempt-history
title: Một học sinh đã làm gì, lúc nào, mất bao lâu
demoable: true
duration: 2d
depends_on: []
requirements: [US-01]
verifies: [AC-01, AC-02]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Một học sinh đã làm gì, lúc nào, mất bao lâu

## Demo script
1. Mở hồ sơ một học sinh: danh sách lượt làm bài với đề, giờ bắt đầu, giờ nộp, số phút, điểm
2. Một lượt bị tự nộp vẫn nằm đó và mang dấu riêng

## In scope
- attempts search read model
- duration on read
- history on the student profile

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-01, AC-02 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
