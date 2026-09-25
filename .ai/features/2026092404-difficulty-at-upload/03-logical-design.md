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

**Kết quả đo, 2026-09-24, `trungtama`, 381 câu dùng được, `qwen2.5:7b`.** Hai lượt: lượt đầu gửi đề trần, lượt
sau gửi kèm phương án (T-02-03, thay đổi sinh ra từ chính lượt đầu).

| | đề trần | kèm phương án |
| --- | --- | --- |
| model đọc được | 380/381 | 381/381 |
| trùng khớp với quy tắc | 35% | 36% |
| lệch một bậc | 46% | 46% |
| lệch ≥ hai bậc | 74 (19%) | 68 (18%) |
| phân bố model | nb 17 · th 30 · vd 46 · vdc 7 | nb 17 · th 27 · **vd 51** · vdc 5 |
| cả lượt | 308s | 366s |

Chỗ lệch ≥ hai bậc **không rải đều mà dồn theo Phần, mỗi Phần một hướng** — đây là thứ con số tổng giấu đi:

| | đề trần | kèm phương án |
| --- | --- | --- |
| Phần I (209) | 47 — model cao hơn 42 | 49 — model cao hơn 38, thấp hơn 11 |
| Phần II (70) | 9 — 3 cao, 6 thấp | **2** |
| Phần III (100) | 17 — thấp hơn **17/17** | 16 — thấp hơn **16/16** |

Ba điều đọc được, và một điều đoán sai:

1. **Phần II là nơi phương án quyết định** (9 → 2). Đề của câu đúng/sai thường chỉ là bối cảnh; bốn mệnh đề mới
   là câu hỏi. Gửi thiếu chúng là gửi thiếu câu hỏi.
2. **Phần III lệch một chiều tuyệt đối, và đó là trần của quy tắc chứ không phải lỗi model.**
   `BY_PART["3"] = ((3,"vd"), (6,"vdc"))` không có cách nào gán `nb` hay `th`, nên một câu trả lời ngắn thực sự
   dễ là thứ quy tắc không với tới được. 0 câu lệch lên trên là hệ quả tất yếu của việc đụng trần.
3. **Giả thuyết về Phần I sai.** Đã đoán 47 câu lệch ở Phần I là do model không thấy phương án. Cho nó thấy rồi:
   tổng không giảm (47 → 49). Cơ chế có thật — hướng "model chấm khó hơn" tụt 42 → 38 — nhưng số câu "model chấm
   dễ hơn hai bậc" tăng 5 → 11: phương án làm model thấy câu dễ đi, chỉ là nó **đi quá** quy tắc chứ không hội tụ
   về quy tắc. Hai bên bất đồng về Phần I vì một lý do khác, chưa biết là gì.

**Chốt: model dẫn ở đâu nó trả lời được, quy tắc lấp phần còn lại — tức giữ nguyên ADR-02.** Không dựa vào độ
chính xác, vì chưa đo được: `difficulty_for(part, number, type)` là hàm thuần của ba thứ đã nằm sẵn trên câu hỏi,
nên nhãn của quy tắc không mang một bit thông tin nào hệ thống chưa có — câu số 3 và số 5 của Phần I vĩnh viễn
cùng mức bất kể nội dung. Nhãn của model là nhãn duy nhất có thông tin mới. Việc của quy tắc là bảo đảm không câu
nào trống mức, không phải làm tín hiệu chính.

**Cái chốt này chưa được kiểm chứng, và phải nói thẳng ra:** mục 4 của báo cáo — đối chiếu tỉ lệ làm đúng thật —
có **mẫu 0 câu**. Cả cơ sở dữ liệu có 1 dòng `answer_facts`. Đồng thuận không phải độ chính xác: hai tín hiệu
cùng sai một kiểu vẫn cho đồng thuận cao. Phải đo lại khi học sinh đã làm bài thật, và việc phải theo dõi là
model dồn về `vd` ngày một đậm (46% → 51%); script tự cảnh báo ở ngưỡng 70%.

**Đo lần hai, 2026-09-25, sau khi lệnh điền chạy thật: mức độ model gán KHÔNG phải thuộc tính của câu hỏi.**

Lệnh điền đã gán `ai` cho cả 379 câu (4 lượt × 100, lượt thứ năm báo `filled: 0`). Nhưng phân bố nó tạo ra lệch
hẳn so với phân bố báo cáo đã đo một giờ trước — `vdc` 47 so với 18–22. Truy bằng bốn lượt, mỗi lượt đổi **một**
biến, và so **từng câu** chứ không so phân bố:

| Hai lượt được so | Giống nhau từng câu |
| --- | --- |
| cùng cấu hình hoàn toàn | **99%** (376/381) |
| chỉ đổi cách đánh số câu trong prompt | **80%** (304/381) |
| báo cáo so với đường lệnh điền | **49%** (184/379) |

Đọc ra ba điều, và điều thứ ba là điều đắt nhất:

1. **Model gần như tất định.** 99% ở lượt đối chứng. Mọi biến động còn lại là do prompt khác nhau, không do model.
2. **Số câu trong prompt là một tín hiệu thật, không phải nhãn để ghép.** Đổi riêng nó làm 77 câu đổi mức. Trước
   đó đã khẳng định ngược lại — "prompt's number chỉ là nhãn để ghép" — và đó là một khẳng định sai, dựa trên việc
   đọc prompt chứ không phải đo nó.
3. **Phần còn lại của khoảng cách (80% → 49%) đến từ việc câu nào nằm cùng lô.** Báo cáo xếp theo `part, number`
   nên một lô là mười câu cùng phần; lệnh điền xếp theo `created_at` nên một lô trộn các phần. Model được hỏi mười
   câu một lúc thì nó **so chúng với nhau**, nên mức của một câu phụ thuộc vào láng giềng của nó.

Hệ quả cho ADR-03: lập luận "model dẫn vì nó là tín hiệu duy nhất đã đọc câu hỏi" **yếu hơn** những gì đã viết ở
trên. Model đọc câu hỏi, *và* số thứ tự tuỳ tiện gán cho nó, *và* chín câu tình cờ nằm cùng lô. Chỉ một trong ba
thứ đó là thuộc tính của câu hỏi.

Và một sai sót về phương pháp đáng ghi lại: khoảng cách này suýt bị bỏ qua vì **phân bố tổng vẫn ổn định** qua các
lượt (`vd` 51–52% ở cả ba) trong khi từng câu thì đổi tới 20–51%. Đã dựa vào phân bố để kết luận "đánh số vô hại",
và kết luận ấy sai. Đây là lần thứ tư trong dự án này một con số tổng nói dối về thứ nó tổng hợp.

**Chưa chốt, cần chủ dự án quyết:** lô 10 câu thì nhanh nhưng mức của một câu phụ thuộc láng giềng; hỏi từng câu
một thì mức là thuộc tính của chính câu ấy nhưng đắt hơn. 379 nhãn đang nằm trong ngân hàng là sản phẩm của một
cách chia lô tuỳ tiện, nên không lặp lại được — chúng nên bị xoá và gán lại sau khi chốt, và chỉ những nhãn
`difficulty_source = 'ai'` bị chạm tới.

### ADR-04 — `manual` là bất khả xâm phạm
**Status:** accepted
Không lượt tách lại, không lệnh điền, không lượt model nào được đổi một mức độ mang dấu `manual`. Một giáo viên
sửa mức độ rồi thấy nó bị đổi lại ở lần tách sau là cách nhanh nhất để họ thôi sửa.
