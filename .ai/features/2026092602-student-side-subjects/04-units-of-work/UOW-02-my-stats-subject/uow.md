---
id: UOW-02
slug: my-stats-subject
title: Tiến độ của tôi đọc được khi có nhiều môn
demoable: true
duration: 2d
depends_on: []
requirements: [US-02]
verifies: [AC-04, AC-05, AC-06, AC-07]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Tiến độ của tôi đọc được khi có nhiều môn

## Demo script
1. Bộ chọn môn mặc định Mọi môn; chọn một môn thì cả bốn khối theo môn ấy
2. Lịch sử ôn tập gập lại được và nói còn bao nhiêu lượt nữa

## In scope
- bộ chọn môn trên trang tiến độ
- lịch sử ôn tập gập và lọc

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-04, AC-05, AC-06, AC-07 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
