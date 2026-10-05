---
feature: 2026092601-exam-labels-and-roster-fill
gate: G2
---

# Logical design

## Approach

Hai trong ba việc **không cần một dòng API nào**. Đáng nói ra, vì nó cho biết lỗi nằm ở đâu:

| Việc | Đã có sẵn | Thiếu gì |
| --- | --- | --- |
| Môn & Lớp của đề | `POST /exams` và `PATCH /exams/{id}` nhận cả hai từ đầu | web chưa bao giờ hỏi |
| Thêm cả lớp cũ | `POST /classes/{id}/members` nhận **danh sách** `user_ids`; `POST /classes/search`; `POST /users/search` lọc theo `class_id` | một hộp thoại chỉ biết tìm từng em |
| Ô đề ôn cá nhân | `assignments.open_at/close_at`, `latest_review` đã trả `title` + `assignment_id` | read model bỏ ngày tháng, chỉ lấy 1 lượt; web bỏ nốt tên đề |

Chỉ việc thứ ba động tới API, và cũng chỉ là **đọc thêm cột đã có** trên một truy vấn đã chạy.

## Alternatives considered

| Cân nhắc | Vì sao không |
| --- | --- |
| Suy khối lớp từ `grade` của các câu trong đề | Một đề thi thử rút từ cả ba khối; con số suy ra là nguồn sự thật thứ hai, và nó trưng lên như thể giáo viên đã chọn (ADR-01) |
| Bắt buộc chọn Môn và Lớp mới tạo được đề | Một đề nháp chưa biết dạy khối nào vẫn phải tạo được (A-02) |
| Liệt kê mọi đề ôn cá nhân trong ô của trang lớp | 25 học sinh × 3 lượt làm bảng cao gấp ba, mà câu hỏi thường trực chỉ là "em ấy đang phải làm đề nào" (ADR-02) |
| Thêm guard chặn đổi môn khi đề đã có câu hỏi | Cấm quá tay một việc không làm hỏng dữ liệu; báo cáo theo môn đọc từ câu hỏi chứ không từ đề (ADR-03) |
| Gộp "thêm từ lớp cũ" vào "Chuyển năm học" | Hai phạm vi khác nhau — cả năm theo quy tắc tên, và đúng một lớp do người dùng chỉ (ADR-04) |
| Mở màn hình rollover ngay từ trang lớp | Nó thao tác trên cả năm học; mở từ một lớp là nói dối về phạm vi |

## Failure modes

| Trường hợp | Mã | Màn hình làm gì |
| --- | --- | --- |
| Môn không thuộc tổ chức | 422 `Invalid` (`subject_id`) | lỗi trên chính ô chọn |
| Lớp đích không tồn tại / khác tổ chức | 404 `NotFound` | toast, hộp thoại đóng |
| Thêm thành viên trùng | không phải lỗi | `add_members` idempotent (A-07) |
| Lớp nguồn rỗng | không phải lỗi | danh sách nói "Lớp này chưa có học sinh" |

## ADRs

### ADR-01 — Môn và Lớp là thứ giáo viên đặt, không suy từ câu hỏi

**Status:** accepted

Suy `grade` từ các câu trong đề chạy được: câu hỏi nào cũng có `grade`. Nhưng một đề thi thử THPT rút từ cả ba
khối, nên con số suy ra sẽ là một cái trung bình vô nghĩa hoặc một khoảng; và tệ hơn, nó **trưng lên như thể
giáo viên đã chọn**. Đúng lỗi mà `difficulty_source` của F22 đã phải sửa: một nhãn máy đoán và một nhãn người
đặt không được nhìn giống nhau.

Đặt tay cũng có cái giá: 36 đề seed sẽ còn trống mãi. Chấp nhận — chúng là dữ liệu dựng thử, và điền bừa một
khối vào sẽ làm chính bản kiểm chứng của việc này mất nghĩa.

**Rejected:** suy từ câu hỏi (nguồn sự thật thứ hai); bắt buộc nhập lúc tạo (một đề nháp vẫn phải tạo được).

### ADR-02 — Ô ôn cá nhân: lượt mới nhất đầy đủ, cộng một con số đếm

**Status:** accepted

Ba cách bày:

| Cách | Vì sao không |
| --- | --- |
| Chỉ lượt mới nhất (hôm nay) | im lặng về các lượt trước — đúng chỗ anh vấp |
| Liệt kê hết trong ô | 25 học sinh × 3 lượt làm bảng cao gấp ba, mà câu hỏi thường trực chỉ là "em ấy đang phải làm đề nào" |
| **Mới nhất đầy đủ + "còn N đề trước"** | trả lời câu hỏi thường trực, và **nói ra** rằng còn thứ nữa thay vì giấu |

Read model vì vậy trả về lượt mới nhất **cộng tổng số lượt** — một `COUNT` trên cùng truy vấn, không phải N+1.
Đây là chỗ dễ sai: lấy `limit 1` rồi đếm ở Python sẽ đếm được đúng 1.

**Rejected:** thêm một màn hình liệt kê mọi bài đã giao cho một học sinh — đáng có, nhưng là việc khác, và con
số đếm đã đủ để không ai bị lừa.

### ADR-03 — Đổi môn của đề đã có câu hỏi: cho phép, và nói ra hệ quả

**Status:** accepted

Đổi `subject_id` khi đề đã có câu của môn cũ tạo một trạng thái lệch: ma trận mở cây môn mới, câu cũ vẫn nằm
trong đề. Ba lựa chọn: chặn (guard mới ở API), tự bỏ câu cũ (mất việc của người dùng), hay cho phép và nói rõ.

Chọn cách thứ ba. Lý do: dữ liệu **không** hỏng — báo cáo theo môn đọc `answer_facts.subject_id` lấy từ **câu
hỏi**, không từ đề; `exam.subject_id` chỉ là phạm vi của bộ chọn. Một guard chặn nửa vời sẽ cấm cả trường hợp
hợp lệ (đề đang trống câu của môn cũ vì vừa xoá hết) để phòng một trường hợp không làm hỏng gì.

**Rejected:** guard ở `update_exam` (cấm quá tay, và API này cố tình không có `guard_edit`).

### ADR-04 — "Thêm từ lớp cũ" đứng cạnh "Chuyển năm học", không thay nó

**Status:** accepted

Repo đã có `commit_rollover`: chuyển **cả năm**, mọi lớp, theo quy tắc tên (10A1 → 11A1), bốn kết cục cho từng
em (lên lớp / ở lại / chuyển trường / tốt nghiệp), tạo lớp đích còn thiếu, ghi trạng thái rời lớp vào bản ghi
cũ, chạy lại không nhân đôi. Việc anh cần là việc **khác**: rót đúng một lớp mới từ đúng một lớp cũ do anh chỉ,
không theo quy tắc tên, không đụng tới năm học.

Nhập hai thứ vào làm một sẽ hỏng cả hai: rollover mất tính "cả năm một lần, ghi được vào sổ", còn việc rót lớp
mất tính "tôi chỉ muốn đúng lớp này". Nên giữ hai đường, và **hộp thoại nói ra đường kia tồn tại** (AC-11) —
vì anh đã đứng ở đây và không biết nó có.

**Rejected:** gộp vào rollover; mở rollover từ trang lớp (nó thao tác trên cả năm, mở từ một lớp là nói dối về
phạm vi).

## Data

Không migration. Ba cột đã có và chưa ai đọc: `exams.grade`, `exams.subject_id` (có, nhưng chỉ script ghi),
`assignments.open_at` / `close_at`.
