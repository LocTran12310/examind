# Con số cạnh dòng ma trận phải là con số máy sẽ dùng

## Problem
Loc Tran, sau khi soạn đề (chat, 2026-09-24, kèm ảnh):

- **"Chọn chuyên đề, có 14 câu, số câu cần là 10, nhưng chỉ tạo được 7 câu, thiếu 3 câu? Không biết lý do là gì
  và làm sao để chọn?"** Đây là một lỗi thật và tôi đã dựng lại: chuyên đề "Mệnh đề" có **14 câu dùng được**, và
  đúng **7** trong số đó là Trắc nghiệm (7 câu còn lại là Đúng/Sai). Dòng ma trận hỏi Trắc nghiệm × 10, nên nó
  lấy được 7. Con số "14" không sai — nó **trả lời một câu hỏi khác** với câu mà dòng ấy đang hỏi, và người dùng
  không có cách nào thấy điều đó.
- **Nhãn xếp hạng.** "Theo chuyên đề (yếu nhất trước)", "Chuyên đề yếu nhất", "Mức nắm vững (cần ôn nhất trước)".
  Loc Tran: *"không thêm label kiểu này, yếu nhất/giỏi nhất, rất dễ rơi vào bẫy tâm lý"*.
- **Nút "Một câu / Toàn đề"** là hai chữ trần, cần icon hoặc chuyển hẳn sang icon kèm tooltip.

## Outcome
---
feature: blueprint-truth
slug: 2026092403-blueprint-truth
owner: Loc Tran
created: 2026-09-24
status: approved
---

## Success signal
Đổi "Loại câu" của một dòng ma trận làm con số bên cạnh đổi theo, và con số ấy **bằng đúng** số câu lệnh tạo đề
lấy được. Không còn màn hình nào gọi một chuyên đề của một học sinh là "yếu nhất".

## Out of scope
- Phân mức độ (NB/TH/VD/VDC) lúc tách đề — 376/378 câu hiện không có mức độ, và Loc Tran chốt để sau
- Đổi cách chọn câu của lệnh tạo đề
- Bỏ ô lọc Mức độ khỏi ma trận

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Giáo viên soạn đề | Thấy 14, được 7, không biết vì sao | Thấy đúng số câu dòng ấy lấy được, và biết ngay cái gì đang chặn |
| Học sinh xem kết quả | Bị dán nhãn "yếu nhất" | Vẫn thấy đúng thứ tự cần ôn, không bị gọi tên |
| Học sinh làm bài | Hai chữ trong thanh chật | Nút có icon và tooltip |

## Constraints
| Kind | Detail |
| --- | --- |
| Data | Không migration |
| Contract | Số câu của một dòng lấy từ đúng bộ lọc mà lệnh tạo đề dùng, không phải một phép đếm gần đúng |
| UI | shadcn; thanh trên của màn làm bài đã chật, icon phải kèm tooltip |
