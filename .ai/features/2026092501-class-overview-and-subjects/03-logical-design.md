---
feature: 2026092501-class-overview-and-subjects
gate: G2
---

# Logical design

## Approach

Ba trong bốn việc là **phơi ra thứ đã có**, không phải tính thêm:

| Việc | Dữ liệu đã có | Thiếu gì |
| --- | --- | --- |
| Lịch sử làm bài | `attempts.started_at`, `submitted_at`, `status`, `score`, `max_score` | không read model nào liệt kê theo học sinh |
| Tổng quan lớp | `answer_facts` (đã có `class_ids`), `attempts`, `assignment_targets.class_id` | không read model nào gộp theo lớp |
| Tách môn ở báo cáo | `/stats/*` **đã nhận `subject_id`** | web chưa bao giờ gửi, và cây không nhóm theo môn |
| Thứ tự menu | — | một dòng trong `nav.ts` |

Không migration nào. Không cột mới nào. Không con số đang có nào đổi.

## Alternatives rejected

- **Lưu sẵn số phút vào `attempts`.** Loại: nó là hiệu của hai cột đã có, và một cột dẫn xuất được lưu là một
  nguồn sự thật thứ hai sẽ lệch vào ngày ai đó sửa `submitted_at` mà quên nó.
- **Nhét lịch sử làm bài vào `/students/{id}/record`.** Loại: `record` là read model của **academic**, nói về năm
  học và học kỳ. Lượt làm bài thuộc **assessment**. Gộp lại là để một module trả lời thay module khác.
- **Ghép tổng quan lớp ở phía client** từ `/assignments/search` rồi gọi `/assignments/{id}/report` cho từng bài.
  Loại: `assignments/search` **không có bộ lọc theo lớp** (chỉ `assignment_targets.class_id` ở tầng dưới), nên
  client sẽ phải tải mọi bài giao của trung tâm rồi tự lọc — đúng cái bẫy đã suýt làm script dọn e2e xoá nhầm bài
  giao thật (`.ai/e2e/README.md`). Và N+1 lời gọi cho một tab.
- **Đổi mặc định của báo cáo sang một môn.** Loại: xem ADR-04.

## Error taxonomy

| Tình huống | Trả lời |
| --- | --- |
| Xem lịch sử của học sinh không thuộc tổ chức | `NotFound` — không xác nhận người đó tồn tại ở nơi khác |
| Học sinh xem lịch sử của bạn khác | `Forbidden`; học sinh chỉ đọc được của chính mình (A-09) |
| Tổng quan của lớp không thuộc tổ chức | `NotFound` |
| Lớp chưa có bài nộp | **không phải lỗi** — trả về rỗng có cấu trúc, màn hình nói "chưa có dữ liệu" (AC-04) |
| `subject_id` không thuộc tổ chức | `Invalid` với tên trường, như mọi bộ lọc khác |

## ADRs

### ADR-01 — Lịch sử làm bài là một list theo đúng hợp đồng search
**Status:** accepted

`POST /api/attempts/search`, body mang `student_id` trong `filters`, trả `{data, total, page, limit}` như mọi
list khác. Không phải `GET /students/{id}/attempts`: hợp đồng của repo nói list là `POST /<resource>/search`, và
tài nguyên ở đây là **lượt làm bài**, không phải học sinh. Chọn thế còn mở sẵn đường cho "mọi lượt của một lớp"
hay "mọi lượt của một bài giao" mà không phải đẻ thêm route.

Phạm vi do actor quyết, không do body: nhân viên đọc được trong tổ chức mình; học sinh bị ép `student_id` về
chính mình. Đây đúng chỗ F20 đã vấp — một trang tên là "của tôi" mà đọc số của cả tổ chức.

### ADR-02 — Số phút tính lúc đọc
**Status:** accepted

`minutes = round((submitted_at − started_at) / 60)`, tính trong read model, không lưu. `null` khi lượt chưa nộp.
Đây là **giờ treo tường của cả lượt**, khác hẳn `seconds_spent` của từng câu — cái kia đo thời gian một câu ở
trên màn hình và bị kẹp theo cửa sổ lượt làm (F14 ADR-01). Hai con số trả lời hai câu hỏi khác nhau và màn hình
phải nói rõ đang hiện cái nào.

Một lượt bị worker tự nộp khi hết giờ mang `submitted_at` là hạn cộng thời gian ân hạn, nên số phút của nó xấp xỉ
`duration_minutes` của bài giao. Nó vẫn hiện, có dấu riêng (AC-02): giấu đi thì cột thời gian nói dối về đúng
những lượt đáng chú ý nhất.

### ADR-03 — Tổng quan lớp là một read model, không phải một chồng lời gọi
**Status:** accepted

`GET /api/classes/{class_id}/summary` trả một lần: số bài giao, số lượt đã nộp, điểm trung bình theo thang của
đề, phổ điểm mười cột, và các chuyên đề lớp yếu nhất. Gộp trong SQL vì dữ liệu đã nằm sẵn ở `answer_facts`
(`class_ids`) và `attempts`.

Phổ điểm dùng **đúng mười cột** như báo cáo bài giao (`assignment_report.py:50-52`), để hai màn hình không vẽ hai
hình khác nhau từ cùng một dữ liệu.

### ADR-04 — Bộ chọn môn thêm lựa chọn, không đổi mặc định
**Status:** accepted

Mặc định vẫn là **"Mọi môn"** — đúng thứ báo cáo đang trả lời hôm nay. Đổi mặc định sang một môn là đổi **nghĩa**
của con số trang báo cáo mà không ai được báo: "Tỉ lệ đúng 62%" hôm nay là của cả trung tâm, ngày mai là của
Toán, và không gì trên màn hình nói rằng nó vừa đổi.

Cái sửa cho lo ngại của anh không nằm ở mặc định mà ở **cách trình bày**: ở "Mọi môn", cây chuyên đề nhóm các
mạch dưới môn của chúng. Một môn thì nhìn y như cũ (một khối duy nhất); nhiều môn thì mỗi môn một khối.

Nguồn của danh sách môn là `/api/taxonomy`, cùng chỗ ngân hàng câu hỏi lấy — hai màn hình không được có hai danh
sách môn khác nhau.
