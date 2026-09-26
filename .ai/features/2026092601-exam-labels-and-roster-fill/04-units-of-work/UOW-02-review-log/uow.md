---
id: UOW-02
slug: review-log
title: Ô đề ôn cá nhân nói đủ: đề nào, bao giờ, còn hạn không, mấy đề
demoable: true
duration: 2d
depends_on: []
requirements: [US-02]
verifies: [AC-04, AC-05, AC-06, AC-07]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Ô đề ôn cá nhân nói đủ: đề nào, bao giờ, còn hạn không, mấy đề

## Demo script
1. Tab Tổng quan của lớp: ô của một em hiện tên đề, ngày giao, hạn và trạng thái
2. Một em quá hạn mà chưa nộp thì nhìn ra ngay
3. Em được giao ba đề thì ô nói còn 2 đề trước đó

## In scope
- read model trả ngày tháng và số lượt
- ô trên bảng tổng quan lớp

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
