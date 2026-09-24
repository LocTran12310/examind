---
feature: difficulty-at-upload
adrs: 4
---

# Logical design

## Approach

Bộ máy đã có gần đủ. Pipeline tách đề đã chạy một lượt model để gắn chuyên đề, với đủ prompt, chia lô, đọc JSON,
chọn model của tổ chức, và cách xuống thang khi model hỏng (`application/tagging.py`, `domain/services/topic_rules.py`,
`application/stages/topic_suggest.py`). Việc ở đây là **một lượt nữa cùng hình dạng**, cho một câu hỏi khác —
"câu này ở mức nào" thay vì "câu này thuộc chuyên đề nào" — cộng một quy tắc thuần để không bao giờ bỏ trống.

**Hai tín hiệu, hai bản chất khác nhau, và thiết kế phải tôn trọng sự khác nhau ấy.**
- *Vị trí trong đề* là một **quy ước**: đề THPT 2025 xếp Phần I trắc nghiệm trước, rồi Phần II đúng/sai, rồi Phần
  III trả lời ngắn, và độ khó tăng dần trong mỗi phần. Nó tất định, miễn phí, không bao giờ vô lý — và không biết
  gì về nội dung câu hỏi. `part` và `number` đã nằm sẵn trên mọi câu ngay lúc `draft_of` chạy.
- *Model* **đọc** được câu hỏi, nên đúng hơn khi nó đúng, và sai một cách tự tin khi nó sai.

Nên: model dẫn khi nó trả lời, quy tắc vị trí lấp phần còn lại, và **không câu nào rỗng** (ADR-02). Ai dẫn là một
hằng số, và hằng số ấy chỉ được chốt **sau khi đo** (ADR-03).

**Dấu vết.** `questions.difficulty_source`: `auto` (quy tắc vị trí) · `ai` (model) · `manual` (người). Đúng khái
niệm mà `question_topics.source` đang mang, nay cho một trường vô hướng. Nó là thứ làm cho "gán thẳng" không
nguy hiểm: một con số máy đoán trông y hệt một con số người đặt, cho tới khi có cột này.

**Điền cho câu cũ.** Một lệnh chạy lại được, chỉ chạm câu `difficulty IS NULL`, dùng đúng hai tín hiệu ấy. Không
đụng tới câu đã có mức độ, bất kể dấu vết là gì.

## Alternatives rejected

- **Đọc mức độ từ văn bản đề.** Không đề nào trong 18 đề mẫu ghi mức độ; không có gì để đọc.
- **Chờ số liệu làm bài rồi mới gán.** Tỉ lệ đúng là thứ duy nhất *đo* được độ khó, nhưng cần ≥10 lượt trả lời
  mỗi câu (`item_stats.MIN_OBSERVATIONS`). Ngân hàng của Loc Tran gần như chưa có lượt nào, nên chờ nghĩa là
  không bao giờ có. Nó là bước **sửa lại** về sau, không phải bước gán đầu tiên; tiền lệ ghi ngược từ thống kê
  vào câu hỏi đã có sẵn ở `key_audit`.
- **Chỉ gợi ý, chờ giáo viên duyệt từng câu.** 374 câu là 374 lượt bấm, và ma trận vẫn rỗng tới khi duyệt xong.
  Loc Tran đã chọn gán thẳng; cột dấu vết là thứ khiến lựa chọn ấy quay lại được.
- **Để model tự do trả lời mọi câu, bỏ quy tắc vị trí.** Model bỏ sót là chuyện thường (lần gắn chuyên đề, độ phủ
  ban đầu là 18%), và một câu rỗng thì ma trận lại không lọc được — đúng chỗ đau ban đầu.

## Error taxonomy

Không có mã lỗi mới. Model hỏng là một **cảnh báo** trong nhật ký của đề, không phải lỗi: đề vẫn tách xong, mọi
câu vẫn có mức độ. Đây đúng cách lượt gắn chuyên đề đang xử lý.

## ADRs

### ADR-01 — Dấu vết là một cột trên `questions`, không phải một bảng gợi ý
**Status:** accepted
`difficulty_source` (`auto` / `ai` / `manual`), nullable cho các dòng viết trước migration. Một bảng gợi ý riêng
sẽ phải đồng bộ với trường thật, và ngày chúng lệch là ngày không ai tin được cả hai. Mọi đường người đặt mức độ
— tạo câu, sửa câu, thanh công cụ hàng loạt, hoàn tác — đều ghi `manual`.

### ADR-02 — Model dẫn, quy tắc vị trí lấp, không bao giờ để trống
**Status:** accepted
Một câu rỗng chính là vấn đề ban đầu, nên độ phủ phải là 100% sau mỗi lần tách. Quy tắc vị trí bảo đảm điều đó mà
không cần model chạy được. Lượt model là thứ nâng chất lượng, không phải thứ tính năng phụ thuộc vào.

### ADR-03 — Đo trước khi chốt ai dẫn
**Status:** accepted
`scripts/difficulty_report.py` chạy cả hai tín hiệu trên ngân hàng thật và báo: độ phủ của model, mức độ đồng
thuận giữa model và quy tắc vị trí, phân bố mỗi bên, và — ở những câu đã đủ 10 lượt trả lời — đối chiếu với tỉ lệ
đúng thật. Con số ấy được đọc **trước khi** chốt hằng số "ai dẫn", và được ghi vào review cuối. Đây là đúng cách
F15 đã làm với chuyên đề, và là lý do lần ấy phát hiện prompt sai khiến độ phủ 18%.

### ADR-04 — `manual` là bất khả xâm phạm
**Status:** accepted
Không lượt tách lại, không lệnh điền, không lượt model nào được đổi một mức độ mang dấu `manual`. Một giáo viên
sửa mức độ rồi thấy nó bị đổi lại ở lần tách sau là cách nhanh nhất để họ thôi sửa.
