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

**Đo lần ba, 2026-09-25, sau khi dựng lại toàn bộ từ cơ sở dữ liệu trắng: hai lỗi thật, và hai lý do tôi đã viết
sai ở trên.**

Việc xoá sạch rồi upload lại 18 đề làm lộ hai thứ mà không phép đo nào trước đó thấy được:

1. **Image `examind-worker` cũ 34 giờ, và worker mới là thứ chạy pipeline.** Mỗi lần build lại chỉ build `api`.
   Nên bước gán mức độ **chưa từng chạy** trong stack thật. Bằng chứng: xoá DB, upload lại 18 đề mà không sửa gì →
   396/397 câu không có mức nào, kể cả quy tắc vị trí. Vậy câu "379 câu trống mức vì pipeline chỉ gán cho thứ nó
   tách" ở trên là **sai lý do**: chúng trống vì worker không có code gán mức.
2. **Số câu THPT lặp lại theo phần, và `ask` ghép trả lời bằng `{số: khoá}`.** Phần I là câu 1–12, Phần II là
   1–4, Phần III là 1–6 trong cùng một đề. Một lô gồm Phần I 11,12 + Phần II 1–4 + Phần III 1–4 thì Phần III ghi
   đè Phần II, và prompt còn tự hỏi "cho các câu: 11, 12, 1, 2, 3, 4, 1, 2, 3, 4". Sau lượt tách đầu tiên chạy
   thật: `ai` 322, `auto` 74 — và **toàn bộ 72 câu Phần II đều `auto`**, đúng 4 câu × 18 đề. Cùng lỗi ở lượt
   chuyên đề (`TopicModelPass.ask`), nhưng ở đó quy tắc dẫn nên nó bị che: Phần II vẫn có chuyên đề 97%.

Sửa ở T-02-04: `ask` tự đánh số theo vị trí trong lô, và `Row` không còn mang số — va chạm trở thành **không biểu
diễn được** chứ không chỉ được tránh. Test hồi quy đã được xem đỏ trên code cũ trước khi xanh: `{'1': 2, '2': 4}`
trên một đề 22 câu.

**Và điều này bác bỏ lập luận tôi dùng để đề xuất "hỏi từng câu một".** Ở trên có viết rằng lệch 49% giữa báo cáo
và lệnh điền là do "câu nào nằm cùng lô". Một phần của nó thật ra là **lỗi mất câu trả lời** vừa nêu, không phải
hiệu ứng láng giềng. Chưa đo lại được phần nào là hiệu ứng láng giềng thật sau khi sửa, nên **chưa chốt** chuyện
lô 10 câu so với từng câu một, và không được dựa vào con số 49% ấy nữa.

**Đo sau khi sửa, cùng ngày, trên ngân hàng vừa dựng lại.** Lượt tách chạy đúng lần đầu tiên:

| | trước bản sửa | sau bản sửa |
| --- | --- | --- |
| câu có mức | 396/397 | **396/396** |
| `ai` / `auto` | 322 / 74 | **396 / 0** |
| Phần II nhận mức từ model | **0/72** | **72/72** |

Phân bố pipeline tạo ra: nb 63 (16%) · th 112 (28%) · vd 179 (45%) · vdc 43 (11%). Mức trung bình theo phần, trên
thang nb=0…vdc=3: **Phần I 1,05 → Phần II 1,94 → Phần III 2,14**.

Con số cuối ấy là **bằng chứng thật đầu tiên cho ADR-03**, thay cho lập luận. Bản sửa đã bỏ số câu khỏi prompt,
nên model không còn biết câu nằm đâu trong đề — vậy mà nó vẫn tự xếp Phần III khó hơn Phần I, đúng thứ tự mà quy
ước đề ngụ ý. Nó đọc nội dung, không đọc vị trí. (Vẫn không nói được nó **đúng** ở từng câu: mục 4 vẫn mẫu 0.)

**Và câu hỏi còn treo đã có số: hiệu ứng láng giềng là thật, và lớn.** So từng câu giữa nhãn pipeline đã ghi và
một lượt báo cáo trên cùng ngân hàng — hai đường giờ dùng prompt giống nhau hoàn toàn, chỉ khác **câu nào nằm cùng
lô** (báo cáo xếp theo `part, number` xuyên các đề; pipeline xếp theo từng đề):

| Hai lượt được so | Giống nhau từng câu |
| --- | --- |
| cùng cấu hình hoàn toàn | 99% |
| khác cách chia lô (sau khi sửa) | **58%** |

Nên lỗi đánh số chỉ giải thích 9 điểm trong khoảng 49% → 58%. Phần còn lại là chính hiệu ứng láng giềng: **chín
câu tình cờ nằm cùng lô đổi mức của một câu trong khoảng 42% trường hợp.** Muốn mức độ là thuộc tính của câu hỏi
thì lô phải là một câu.

**Đo lô một câu, cùng ngày. `DIFFICULTY_BATCH` chốt về 1.**

| | lô 10 câu | **lô 1 câu** |
| --- | --- | --- |
| Hai lượt cùng cấu hình giống nhau từng câu | 99% | **100%** (376/376) |
| Trùng khớp quy tắc vị trí | 36% | 41% |
| Lệch ≥ hai bậc | 18% | 11% |
| Phân bố model | nb 19 · th 20 · **vd 56** · vdc 6 | nb 29 · th 26 · **vd 18** · vdc 28 |
| Phần III lệch ≥2 bậc | 16%, một chiều 16/16 | **1%** (1 câu) |
| Cả ngân hàng | ~320s | 464s (**+45%**) |

Ba điều, và điều thứ nhất là điều quyết định:

1. **Tất định hoàn toàn, và mức độ trở thành thuộc tính của câu hỏi.** Prompt chỉ chứa câu ấy, nên không còn gì để
   phụ thuộc vào. 100% là đo hai lượt, không phải suy ra từ việc prompt giống nhau.
2. **Việc model dồn 56% vào `vd` là artefact của việc chia lô, không phải của model.** Hỏi mười câu một lúc thì nó
   so chúng với nhau và tụ về nhãn giữa; hỏi từng câu thì nó dùng cả bốn bậc (`vdc` 6% → 28%). Một tín hiệu dùng
   hết thang đo mang nhiều thông tin hơn một tín hiệu nói `vd` cho nửa ngân hàng — lập luận này không cần biết ai
   đúng.
3. **Thiên lệch hệ thống theo Phần biến mất.** Phần III từ 16 câu lệch **cùng một chiều** xuống còn 1 câu; Phần I
   thành đối xứng (16 lên, 16 xuống), tức chỉ còn nhiễu.

**Prompt không được đổi một chữ.** Con số 100% ở trên đo đúng `DIFFICULTY_SYSTEM` hiện tại; sửa lời prompt là làm
phép đo ấy hết giá trị.

**Tách lại toàn bộ 18 đề với nhãn lô-1 (2026-09-25):** 396/396 câu có mức, **`ai` 396 / `auto` 0** — lần đầu tiên
không câu nào phải rơi về quy tắc. Phân bố pipeline nb 29% · th 25% · vd 17% · vdc 29%, **khớp phép đo của
`difficulty_report.py`** (29/26/18/28) vì hai đường giờ dùng chung một cách hỏi. Mức trung bình theo phần trên
thang nb=0…vdc=3: **Phần I 0,68 → Phần II 1,69 → Phần III 2,87**, dốc hơn hẳn lô 10 (1,05 → 1,94 → 2,14) — và
model vẫn không được cho biết vị trí câu trong đề.

### ADR-04 — `manual` là bất khả xâm phạm
**Status:** accepted
Không lượt tách lại, không lệnh điền, không lượt model nào được đổi một mức độ mang dấu `manual`. Một giáo viên
sửa mức độ rồi thấy nó bị đổi lại ở lần tách sau là cách nhanh nhất để họ thôi sửa.
