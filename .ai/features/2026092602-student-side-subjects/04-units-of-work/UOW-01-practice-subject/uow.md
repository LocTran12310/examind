---
id: UOW-01
slug: practice-subject
title: Đề ôn tập mang môn của nó
demoable: true
duration: 2d
depends_on: []
requirements: [US-01]
verifies: [AC-01, AC-02, AC-03]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Đề ôn tập mang môn của nó

## Demo script
1. Học sinh bấm Tạo đề ôn tập, chọn môn, đề sinh ra mang đúng môn ấy
2. Trung tâm một môn thì không hỏi, đề vẫn có môn

## In scope
- subject qua cổng analytics tới exams.subject_id
- bước chọn môn ở nút tạo đề

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-01, AC-02, AC-03 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
