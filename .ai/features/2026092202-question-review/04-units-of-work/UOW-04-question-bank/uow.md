---
id: UOW-04
slug: question-bank
title: Teachers search, edit and create questions in the bank
demoable: true
duration: 2d
depends_on: [UOW-01]
requirements: [US-06, US-03]
verifies: [AC-10, AC-15, AC-16, AC-17, AC-18, AC-19, AC-20]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-04 — Teachers search, edit and create questions in the bank

## Demo script
1. Open /org/bank, search 'parabol', filter Lớp 10 and topic 'Đại số' → vertex questions listed
2. Open one, edit solution, add a tag, change difficulty → saved and rendered
3. Click 'Thêm câu hỏi', paste an image into the stem, save → appears as approved manual
4. Select 3 questions → set difficulty 'Vận dụng' in bulk
5. Delete a question; filter 'Đã loại' → restore a rejected one

## In scope
- Search/filter/create/delete/bulk API
- Bank list with filters
- Question editor with image upload
- Bulk actions

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-10, AC-15, AC-16, AC-17, AC-18, AC-19, AC-20 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
