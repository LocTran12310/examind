---
feature: 2026092602-student-side-subjects
gate: G2
---

# Logical design

## Approach

Phần lớn đường ống **đã có**, và đó là điều đáng nói nhất:

| Mảnh | Đã có | Thiếu |
| --- | --- | --- |
| Lọc kế hoạch ôn theo môn | `StartPractice.subject_id` → `PracticePlanner.build(..., subject_id)` | web không gửi |
| Ghi môn lên đề | `exams.subject_id` (cột), `CreateExam` của assessment nhận `subject_id` | cổng `Assessment.create_exam` phía analytics **không có tham số môn** |
| Số liệu theo môn | `/stats/topics`, `/stats/groups` nhận `subject_id` từ F23 | trang "của tôi" không gửi |
| Nhóm chuyên đề theo môn | `TopicStatsTree` nhận `subjects` | trang "của tôi" không truyền |

Nên việc thật sự phải viết chỉ có ba chỗ: **một tham số xuyên qua cổng analytics**, **một bước chọn môn ở nút
tạo đề**, và **một bộ chọn môn trên trang tiến độ** kéo theo cả bốn khối.

## Alternatives rejected

| Cân nhắc | Vì sao không |
| --- | --- |
| Suy môn của đề ôn từ các câu trong nó | Không cần suy: kế hoạch được dựng **trong phạm vi một môn**, nên môn là thứ đã biết lúc tạo. Suy lại là dựng nguồn sự thật thứ hai (ADR-01) |
| Điền môn cho 95 đề ôn cũ | Đoán hộ quá khứ; "không rõ môn" thật thà hơn một nhãn bịa (A-08) |
| Tab theo môn trên trang tiến độ | Anh chọn bộ chọn; và tab ép học sinh luôn ở trong một môn, còn "Mọi môn" mới là câu trả lời cho "tôi đang yếu ở đâu" |
| Bắt giáo viên chọn môn khi giao đề ôn cho cả lớp | Luồng khác, chưa ai kêu; đổi cùng lúc là trộn hai thay đổi vào một (ADR-02) |
| Cho ẩn hẳn từng lượt ôn trong lịch sử | "Ẩn" mà mất hẳn là xoá dữ liệu học tập của chính em ấy; thứ thiếu là **thu gọn**, không phải xoá (A-06) |

## Error taxonomy

| Trường hợp | Mã | Màn hình làm gì |
| --- | --- | --- |
| Môn không thuộc tổ chức | 422 `Invalid` (`subject_id`) | lỗi ngay trên bước chọn môn |
| Ngân hàng của môn ấy không có câu dùng được | 409 `empty_bank` | nói rõ là môn ấy chưa có câu, không phải "lỗi" |
| Không phải học sinh | 403 | nút không hiện với vai khác (đã thế từ trước) |

## ADRs

### ADR-01 — Môn của đề ôn tập là thứ **được chọn**, không phải thứ suy ra

**Status:** accepted

Kế hoạch ôn được dựng trong phạm vi một môn: `PracticePlanner.build` nhận `subject_id` và chỉ bốc câu của môn
ấy. Nên lúc tạo đề, môn là **dữ kiện đã biết** — ghi nó lên `exams.subject_id` là ghi lại một sự thật, không
phải đoán. Suy ngược từ các câu trong đề sau đó sẽ ra cùng một con số trong 99% trường hợp và **sai** trong 1%
còn lại (đề cũ trộn môn), mà 1% ấy lại chính là chỗ người đọc cần tin nhất.

Giá phải trả: cổng `Assessment.create_exam` phía analytics phải thêm một tham số. Đó là một cổng nội bộ giữa hai
context, không phải hợp đồng HTTP — đổi nó rẻ hơn nhiều so với một nguồn sự thật thứ hai.

### ADR-02 — Chỉ đổi luồng học sinh tự ôn, không đụng luồng giáo viên giao

**Status:** accepted

`POST /classes/{id}/adaptive-assignments` cũng tạo đề `adaptive`, cũng không có môn. Cám dỗ là sửa luôn cả hai.
Không: giáo viên **chưa có** chỗ nào để chọn môn trong luồng ấy, nên "sửa luôn" nghĩa là tự nghĩ ra một mặc định
cho một màn hình chưa ai kêu — và nếu nghĩ sai thì hỏng một việc đang chạy được để chữa một việc chưa ai hỏi.
Ghi lại ở `00-intent.md › Out of scope` để lần sau không phải tìm lại lý do.

### ADR-03 — Bộ chọn môn áp cho **cả bốn khối**, hoặc không nên có

**Status:** accepted

Trang tiến độ có bốn khối số: mức nắm vững, theo chuyên đề, theo loại câu, lịch sử ôn tập. Một bộ chọn chỉ áp
cho hai khối đầu là cái bẫy đọc số tệ nhất có thể bày ra: người đọc chọn "Toán" rồi đọc một con số của mọi môn
mà không có gì trên màn hình nói ra điều đó. Nên hoặc cả bốn theo môn, hoặc đừng làm bộ chọn.

Lịch sử ôn tập lọc được **vì** từ nay mỗi lượt mang môn của nó (ADR-01); lượt cũ không có môn thì **không rơi
vào** bất kỳ môn nào khi đang lọc, và nói rõ là "không rõ môn" chứ không bị gán bừa (AC-07).

## Data

Không migration. `exams.subject_id` đã có cột từ đầu; thay đổi duy nhất là từ nay có người ghi vào nó cho đề
`adaptive`.
