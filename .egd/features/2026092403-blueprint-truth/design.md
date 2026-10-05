---
feature: blueprint-truth
adrs: 3
---

# Logical design

## Approach

**Con số.** Hôm nay dòng ma trận đọc `counts[topic_id]` từ một lần gọi `POST /questions/facets` cho cả môn
(`use-blueprint-editor.ts: held()`), còn lệnh tạo đề lại lấy câu qua `BankApi.pool(...)` với
`status="usable"` **cộng** loại câu và mức độ của chính dòng đó. Hai phép đếm khác nhau, và "14 câu → tạo được 7"
là lần lệch đầu tiên lộ ra. Cách sửa không phải là sửa con số cho khớp, mà là **hỏi đúng câu hỏi**: mỗi dòng hỏi
số câu của chính bộ lọc của nó, qua `POST /questions/search` với `{topic_id, type, difficulty, status: "usable",
limit: 1}` và đọc `total`. Đó là cùng một phép lọc mà pool dùng, nên hai con số không thể lệch nhau nữa.

Dòng cũng cần con số **không lọc** để nói được câu "chuyên đề có 14, hợp dòng này 7" — vẫn là `counts[topic_id]`
đang có, nên giữ nguyên nó và thêm phép đếm theo dòng bên cạnh.

**Nhãn.** Ba chỗ, bỏ cách gọi tên chứ không đổi thứ tự: `AttemptResult/ResultView` ("Theo chuyên đề (yếu nhất
trước)"), `ClassDetail/ClassOverview` (cột "Chuyên đề yếu nhất"), `MyStats/MyStatsPage` ("Mức nắm vững (cần ôn
nhất trước)"). Thứ tự sắp xếp là thông tin; gọi một đứa trẻ là "yếu nhất" thì không.

**Nút chế độ.** `ToggleGroup` trong thanh trên của `Runner` nhận icon cho mỗi chế độ và một tooltip.

## Alternatives considered

- **Sửa `facets` để nó nhận loại câu và mức độ rồi vẫn trả map theo chuyên đề.** Làm được, nhưng vẫn là phép đếm
  thứ hai đi song song với pool, và vẫn có thể lệch lần nữa. Hỏi thẳng cái pool đếm là hết đường lệch.
- **Đếm ở phía client từ danh sách câu đã tải.** Trang không tải cả ngân hàng, và sẽ không bao giờ nên tải.
- **Bỏ con số đi cho khỏi sai.** Con số ấy chính là thứ giúp không dựng một dòng vô vọng; bỏ nó là quay lại chỗ
  F17 đã sửa.
- **Giữ nhãn nhưng làm nhẹ đi ("cần chú ý").** Vẫn là xếp hạng, chỉ lịch sự hơn. Thứ tự đã nói đủ.

## Failure modes

Không có mã lỗi mới. Một dòng không đủ câu vẫn là `shortfalls` như hôm nay; chỉ phần chữ trên màn đổi.

## ADRs

### ADR-01 — Con số của một dòng hỏi đúng cái mà lệnh tạo đề hỏi
**Status:** accepted
Mỗi dòng gọi `POST /questions/search` với chính bộ lọc của nó và đọc `total`. Tốn một request nhỏ cho mỗi dòng,
đổi lại con số trên màn và con số lệnh tạo đề dùng là **một**. Một phép đếm gần đúng chạy song song là thứ đã gây
ra chính lỗi này.

### ADR-02 — Thứ tự là thông tin, tên gọi thì không
**Status:** accepted
Các danh sách theo chuyên đề vẫn xếp "cần ôn trước lên trên" — đó là thứ giúp người học biết bắt đầu từ đâu. Cái
bỏ đi là dòng chữ tuyên bố một chuyên đề là yếu nhất của một người. Với một học sinh, một nhãn như vậy là một
phán quyết; cùng thông tin ấy, không có nhãn, vẫn dùng được y nguyên.

### ADR-03 — Icon kèm tooltip, không thay chữ bằng icon trần
**Status:** accepted
Thanh trên của màn làm bài đã chật, nhưng hai icon không nhãn trong một thanh mà học sinh chỉ gặp vài lần thì
phải đoán. Icon **cộng** chữ ở màn rộng, và tooltip ở mọi màn.
