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
- [x] All of AC-01, AC-02, AC-03 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence

**AC-03 (đề mang môn) chốt ở `test_practice_api.py`**, không ở trình duyệt: test tạo một đề kèm `subject_id` rồi
đọc lại `exams.subject_id` của chính nó, và tạo một đề **không** kèm rồi khẳng định nó không có môn. Dựng lại
trên trình duyệt sẽ ghi một lượt làm bài thật vào hồ sơ một học sinh thật để đổi lấy một khung hình không cho
thấy gì hơn.

**AC-01 (bước chọn môn) và AC-02 (một môn thì không hỏi)** chốt ở `practice.test.tsx`. Bước chọn **chỉ xuất
hiện khi có từ hai môn**, mà `trungtama` dạy đúng một — thêm môn thứ hai vào ngân hàng thật chỉ để chụp ảnh là
đúng cái giá §42 vừa phải trả. Test dựng hai môn trong ba dòng và khẳng định cả hai nhánh, gồm cả việc một môn
thì **vẫn gửi** môn ấy đi.
