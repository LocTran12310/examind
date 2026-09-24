---
id: UOW-01
slug: keep-ids
title: The history keeps the id of a deleted question, and the refusal names it
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02]
verifies: [AC-01, AC-02, AC-03]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — The history keeps the id of a deleted question, and the refusal names it

## Demo script
1. Xóa một câu đã có lịch sử → các dòng review_events của nó vẫn giữ nguyên question_id
2. Hoàn tác lượt sửa có câu đã xóa → từ chối cả lượt và nêu đúng id những câu không phục hồi được
3. Dòng lịch sử cũ (id đã bị xóa trước migration) vẫn đọc được như trước

## In scope
- drop the foreign key
- name the gone questions
- legacy rows unchanged

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

## Verification evidence
Not applicable, and deliberately so: this change is invisible in the browser unless a question is deleted, and
no verification run may delete a question from the owner's bank. The three acceptance criteria are checked where
they can be checked honestly — `apps/api/tests/test_bank_api.py` deletes a question it created and reads its
events back, `apps/api/tests/unit/test_bank_handlers.py` covers the refusal and the rows nulled before the
migration, and `apps/api/tests/test_schema_drift.py` holds the metadata and the database to each other. No
`07-verification.md` is written, so no evidence checkbox is claimed here.
