# phía học sinh cũng phải biết môn

## Problem
Anh hỏi hai câu và chúng dẫn tới cùng một chỗ: **"Tạo đề ôn tập lưu ở đâu? Môn gì?"**

Đề ôn tập lưu **cùng chỗ với mọi đề khác** — một hàng trong `exams`, đánh dấu `source="adaptive"` nên không lọt
vào "Đề thi & giao bài" — kèm một lượt làm bài mở sẵn. Còn môn thì: **không có. 0/95 đề ôn tập có `subject_id`.**

Và đây không phải vì thiếu chỗ chứa. `POST /me/practice` **đã nhận `subject_id`** từ lâu, bộ lập kế hoạch
(`PracticePlanner.build`) đã dùng nó để thu hẹp ngân hàng — chỉ có cái nút "Tạo đề ôn tập" là chưa bao giờ gửi,
và `create_exam` của phía analytics không có chỗ nào để truyền môn xuống. Cùng đúng một hình dạng lỗi với cột
"Lớp" và cột "Môn" của đề (§36, §37): **dữ liệu có chỗ, API nhận, màn hình không hỏi.**

Hệ quả thấy được ngay trên màn hình "Tiến độ của tôi":

- **Mức nắm vững** là một danh sách phẳng cắt cứng ở 8 dòng — với một môn thì đọc được, với bảy môn thì tám dòng
  ấy có thể toàn Toán và học sinh không biết mình yếu Lý.
- **Theo chuyên đề** dùng `TopicStatsTree`, thứ **đã biết nhóm theo môn** từ F23 — nhưng trang không truyền dữ
  liệu môn vào, nên nó vẫn vẽ phẳng.
- **Lịch sử ôn tập** là một danh sách phẳng **không ẩn được, không lọc được** (nguyên văn của anh). Mỗi lượt ôn
  đẻ ra một dòng; làm nhiều đề nhiều môn thì nó dài mãi và không có cách nào thu lại.

## Outcome
---
feature: 2026092602-student-side-subjects
gate: G0
---

## Success signal
Một học sinh ở trung tâm hai môn bấm "Tạo đề ôn tập", chọn môn, và đề sinh ra **mang đúng môn đó** — đọc được
trong lịch sử ôn tập và lọc được theo môn. Trang "Tiến độ của tôi" có bộ chọn môn mặc định "Mọi môn", và chọn một
môn thì cả bốn khối bên dưới đều nói về môn ấy.

## Out of scope
- **Nhóm "Bài được giao" theo môn** ở trang chủ học sinh. Danh sách ấy ngắn (những bài đang mở) và bài giao lấy
  môn từ đề của nó; gộp nhóm ở đó là việc khác, ghi lại chứ chưa làm.
- **Đề ôn cá nhân do giáo viên giao cho cả lớp** (`/classes/{id}/adaptive-assignments`): giáo viên không chọn môn
  ở đó hôm nay. Để nguyên — đổi nó là đổi một luồng khác, và ADR-02 nói vì sao.
- **Sửa 95 đề ôn tập cũ cho có môn.** Suy ngược từ câu hỏi của chúng thì làm được, nhưng đó là đoán hộ quá khứ.

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Học sinh tự ôn | Bấm một nút, nhận một đề không thuộc môn nào | Chọn môn rồi tạo; đề mang đúng môn ấy |
| Học sinh xem tiến độ | Một trang phẳng, tám dòng nắm vững, lịch sử dài mãi | Chọn môn như trang Báo cáo; lịch sử lọc và gập được |
| Trung tâm nhiều môn | Không phân biệt được số liệu của môn nào | Mọi khối trên trang đều thuộc môn đang chọn |

## Constraints
| Kind | Detail |
| --- | --- |
| Contract | `POST /me/practice` đã có `subject_id`; `/stats/topics` và `/stats/groups` đã nhận `subject_id` từ F23 |
| Data | Không migration: `exams.subject_id` đã có cột, chỉ chưa ai ghi vào cho đề adaptive |
| Tenancy | Mọi truy vấn theo `Actor.org_id`; trang "của tôi" luôn tự thu về chính người gọi |
| UI | Bộ chọn môn **giống trang Báo cáo** (quyết định của anh): mặc định "Mọi môn", thêm lựa chọn chứ không đổi mặc định |
