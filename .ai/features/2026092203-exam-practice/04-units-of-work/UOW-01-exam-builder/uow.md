---
id: UOW-01
slug: exam-builder
title: Teachers build exams from blueprints or by hand
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-06]
verifies: [AC-01, AC-02, AC-03, AC-04, AC-05, AC-07, AC-11, AC-15, AC-17, AC-22]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Teachers build exams from blueprints or by hand

## Demo script
1. Staff pages use the new grouped sidebar (also on a 375 px phone as a drawer)
2. Open /org/exams → 'Tạo đề' → title 'Kiểm tra 15 phút', rows (Đại số · Trắc nghiệm · 6), (Hình học · Trắc nghiệm · 4) → 10 questions
3. Add a row that cannot be filled → 'thiếu N câu' warning
4. Swap one question, remove one, add one from bank search, drag to reorder; change MCQ points to 0.5 → total updates
5. 'Xem trước' shows the exam as students see it; toggle answers
6. Try deleting a used question in the bank → 'đang được dùng trong đề'

## In scope
- Schema for exams, assignments, attempts, facts
- Scoring module
- Exams API + blueprint builder
- Sidebar nav
- Exams UI

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-01, AC-02, AC-03, AC-04, AC-05, AC-07, AC-11, AC-15, AC-17, AC-22 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
