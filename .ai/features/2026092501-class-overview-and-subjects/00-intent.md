---
feature: 2026092501-class-overview-and-subjects
gate: G0
---

# Intent — nhìn được cả lớp, và biết một học sinh đã làm gì lúc nào

## Problem

Bốn thứ anh nêu sau khi xem trung tâm 150 học sinh chạy thật:

1. **Không biết một học sinh đã làm những đề nào, lúc nào, mất bao lâu.** Trang hồ sơ chỉ có tổng theo năm học,
   học kỳ và mạch kiến thức. Không endpoint nào liệt kê lượt làm bài của một học sinh — `/students/{id}/record`
   trả số tổng, còn `/attempts/{id}` chỉ đọc được một lượt khi đã biết id của nó. Muốn biết em ấy làm đề nào hôm
   nào thì phải mở từng bài giao một.
2. **Trang lớp chỉ xem được từng em.** "Tình hình học tập" là bảng mỗi em một dòng; muốn biết *cả lớp* thế nào —
   trung bình bao nhiêu, phổ điểm ra sao, lớp yếu chỗ nào — phải sang Báo cáo rồi tự chọn lại đúng lớp ấy.
3. **Thứ tự menu "Lớp & học sinh" không theo trình tự làm việc**: Năm học · Cơ cấu trường · **Người dùng** · Lớp
   học. Lớp nằm sau người dùng trong khi người ta lập lớp trước rồi mới xếp người vào.
4. **Báo cáo theo chuyên đề phẳng theo môn.** Hôm nay chỉ có Toán nên năm mạch kiến thức nằm cạnh nhau là đọc
   được. Thêm môn thứ hai là các mạch của hai môn trộn vào một danh sách không cách nào phân biệt. API thống kê
   **đã nhận `subject_id`** từ lâu; web chưa bao giờ gửi.

## Success signal

- Mở hồ sơ một học sinh thấy ngay danh sách lượt làm bài: đề nào, bắt đầu lúc nào, nộp lúc nào, **mất bao nhiêu
  phút**, được bao nhiêu điểm.
- Mở một lớp thấy được cả lớp mà không phải rời trang: bao nhiêu bài đã giao và đã nộp, điểm trung bình, phổ
  điểm, lớp yếu chuyên đề nào.
- Thêm môn thứ hai vào trung tâm thì báo cáo theo chuyên đề vẫn đọc được — mỗi môn một khối, không trộn.
- Menu đi theo trình tự: Năm học → Cơ cấu trường → Lớp học → Người dùng.

## Out of scope

- **Không đổi cách chấm, cách tính mastery hay bất kỳ con số nào đang có.** Đây là feature *nhìn thấy*, không
  phải feature *tính lại*.
- **Không đo thời gian làm từng câu.** `seconds_spent` đã có và đã bị kẹp theo cửa sổ của lượt làm (thiết kế
  F14); thứ anh hỏi — "từ lúc start đến lúc nộp" — là `submitted_at - started_at`, một phép trừ trên dữ liệu đã
  có, không cần đo thêm gì.
- **Không dựng màn hình so sánh giữa các lớp.** Một lớp một trang; so sánh nhiều lớp là việc của Báo cáo.
- **Không sửa dữ liệu seed để thời gian trông đẹp.** Xem A-03.
