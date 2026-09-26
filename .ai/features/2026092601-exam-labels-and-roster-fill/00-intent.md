---
feature: 2026092601-exam-labels-and-roster-fill
gate: G0
---

# Intent — đề thuộc khối nào, ôn cá nhân đã giao gì, và xếp lớp không phải gõ từng em

## Problem

Ba thứ anh nêu khi đi qua "Đề thi & giao bài", trang lớp và việc lập lớp cho năm học mới.

**1. Cột "Lớp" của danh sách đề trống ở cả 36 dòng.** Không phải lỗi hiển thị: đo trên dữ liệu thật,
**0/131 đề có `grade`**. API nhận `grade` ở cả `POST /exams` lẫn `PATCH /exams/{id}` từ đầu, nhưng **web chưa
bao giờ hỏi** — form "Tạo đề mới" chỉ có một ô Tên đề, còn nút "Sửa" chỉ điều hướng sang trang soạn đề, nơi
cũng không có ô nào cho Môn hay Lớp. Một cột không bao giờ có giá trị cho bất kỳ dòng nào là một cột nói dối
về việc nó đang phân loại thứ gì.

Cùng lỗ hổng ấy áp cho **Môn**, và ở đó hậu quả nặng hơn: 36 đề seed đều có `subject_id` vì script gọi thẳng
API, còn **mọi đề tạo từ giao diện sẽ không có môn** — và ma trận của một đề không môn mở ra cả cây chuyên đề
của mọi môn thay vì môn của nó.

**2. "Đề ôn cá nhân" trên trang lớp chỉ nói Đã làm / Chưa làm.** Anh hỏi đúng bốn câu mà ô ấy không trả lời
được: *đề đã giao là gì · giao từ ngày nào · hết hạn chưa · giao nhiều đề thì sao*. Read model đã đọc sẵn
`title` và `assignment_id` rồi **bị tầng web bỏ đi**; `open_at`/`close_at` thì chưa ai đọc. Và nó lấy đúng
**một** lượt giao gần nhất (`order_by created_at desc limit 1`), nên ba lần bấm "Giao đề ôn cá nhân" nhìn y hệt
một lần — màn hình không sai lộ liễu, nó chỉ im lặng về hai đề kia.

**3. Xếp học sinh vào lớp của năm học mới phải gõ tìm từng em.** Hộp "Thêm học sinh vào lớp" chỉ có một ô tìm
(≥ 2 ký tự) rồi thêm từng em một. Với một lớp 25 em thì đó là 25 lần gõ và 25 lần bấm.

Việc này có sẵn một nửa mà anh không gặp: **"Chuyển năm học"** trên trang Năm học đã chuyển *cả năm* — mọi lớp,
10A1 → 11A1, giữ lại / chuyển trường / tốt nghiệp từng em, tạo lớp đích còn thiếu, chạy lại không nhân đôi. Cái
còn thiếu là việc nhỏ hơn và khác hẳn: **rót một lớp mới từ đúng một lớp cũ**, do người dùng chọn, không theo
quy tắc tên.

## Affected personas

| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Giáo viên xếp đề | Không gắn được đề vào môn hay khối; lọc theo Lớp không bao giờ ra gì | Đặt Môn và Lớp lúc tạo, sửa được sau |
| Giáo viên soạn đề bằng ma trận | Đề tạo từ giao diện không có môn → ma trận mở cả cây mọi môn | Đề có môn → ma trận chỉ mở chuyên đề của môn ấy |
| Giáo viên theo dõi ôn tập | Một chữ "Chưa làm": không biết đề nào, giao bao giờ, còn hạn không | Tên đề, ngày giao, hạn, quá hạn hay chưa, và có mấy đề |
| Giáo vụ lập lớp năm mới | Gõ tìm và bấm 25 lần | Chọn một lớp cũ, thấy cả danh sách, thêm cả lớp trong một lần |

## Success signal

Tạo một đề mới từ giao diện: cột **Lớp có số**, và ma trận của nó chỉ mở chuyên đề của môn đã chọn. Ô "Đề ôn cá
nhân" đọc được thành câu — *đề nào · giao ngày nào · hạn ngày nào · đã làm hay chưa* — và nói ra khi có nhiều
hơn một. Lớp mới nhận đủ học sinh của một lớp cũ trong **một** lần bấm.

## Out of scope

- **Suy khối lớp từ câu hỏi trong đề.** Câu hỏi có `grade` riêng và một đề thi thử THPT rút từ cả ba khối; suy
  ra một con số rồi trưng lên như thể giáo viên đã chọn là dựng nguồn sự thật thứ hai sẽ lệch.
- **Sửa 36 đề seed cho có khối.** Điền bừa sẽ làm chính bản kiểm chứng của việc này mất nghĩa.
- **Màn hình riêng liệt kê mọi bài đã giao cho một học sinh.** Đáng có, nhưng là việc khác; ở đây chỉ cần ô trên
  trang lớp thôi nói thật về số lượng.
- **Thay hay gộp "Chuyển năm học".** Nó giải quyết việc khác (cả năm, theo quy tắc tên, có trạng thái rời lớp).
  Xem ADR-04.
- **Chặn đổi môn khi đề đã có câu hỏi.** Xem ADR-03: nói bằng chữ, không thêm một guard nửa vời.

## Constraints

| Kind | Detail |
| --- | --- |
| Contract | `grade`/`subject_id` đã có trên `POST /exams` và `PATCH /exams/{id}`; `POST /classes/{id}/members` đã nhận **danh sách** `user_ids`. Không đổi hợp đồng nào |
| Data | Không migration: `exams.grade`, `exams.subject_id`, `assignments.open_at/close_at` đều đã có cột |
| Tenancy | Mọi truy vấn theo `Actor.org_id` |
| UI | shadcn qua `OptionSelect`; tiếng Việt trong chuỗi người dùng đọc |
