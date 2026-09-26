---
feature: student-home
environments: [e2e-hs01]
viewports: [desktop, mobile]
---

# Verification — trang chủ học sinh vẫn nguyên khi trung tâm dạy một môn

Nhóm theo môn **chỉ hiện khi một mục có từ hai môn**. Trung tâm này dạy đúng một, nên thứ kiểm được ở đây không
phải cái nhóm — mà là **nó không làm hỏng cái đang chạy**: với một môn, học sinh phải thấy đúng danh sách phẳng
họ vẫn thấy, không thừa một tiêu đề nào. Đó là rủi ro thật của thay đổi này: một vòng lặp mới bọc quanh ba mục,
mỗi mục một cấu trúc khác nhau.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert | Env |
|---|---|---|---|---|---|---|
| S1 | Trang chủ học sinh: có bài để hiện, và không một tiêu đề môn nào | `/home` | `settle 5000` | flat-when-one-subject | `text=Đang mở`; `count [data-testid="open-E2E · bài mẫu"] = 1`; `count [data-testid="open-E2E · bài mẫu"] button:has-text("Bắt đầu") = 1`; `count h3 = 0`; `no-text=Không có bài nào đang mở`; `no-text=Chưa rõ môn`; `no-text=Có lỗi xảy ra` | e2e-hs01 |

**`count h3 = 0` chỉ có nghĩa khi danh sách không rỗng, nên phải giao bài trước.** Lượt chạy đầu của bản này đi
trên một `e2e.hs01` chưa được giao gì: ảnh chụp là trạng thái rỗng ("Không có bài nào đang mở"), và với danh sách
rỗng thì "không có tiêu đề nào" đúng một cách tầm thường — nó không phân biệt được bản dựng nào với bản dựng nào.
Giờ `make e2e-fixture ARGS=--with-exam` giao `E2E · bài mẫu` cho lớp thử, nên ba khẳng định đi cùng nhau mới là
bằng chứng: **có** đúng thẻ bài ấy (`count [data-testid="open-E2E · bài mẫu"] = 1`), **không** có tiêu đề môn
(`count h3 = 0`), và mục không phải trạng thái rỗng (`no-text=Không có bài nào đang mở`). Một bản dựng luôn in
tiêu đề — cách hiển nhiên để viết cái nhóm này — sẽ ra `h3 = 1` và đỏ ở đúng đây.

**Đề của fixture mang môn Toán thật**, không để trống. Nếu để trống thì `subject_id` của bài giao là `null` và
`count h3 = 0` xanh nhờ nhánh "không có môn nào" chứ không nhờ nhánh "một môn" — hai nhánh khác nhau trong
`group-by-subject.ts`, và nhánh đáng kiểm ở trung tâm này là nhánh sau. Đây cũng là đường đi qua `subjects_of`
ở tầng API: một đề không môn thì cái truy vấn ấy không phải trả lời gì.

## Không kiểm ở đây

- **Chính việc nhóm theo môn** (nhiều môn, và bài chưa rõ môn đứng riêng ở cuối) không dựng được ảnh trên trung
  tâm này: nó dạy một môn. Thêm môn thứ hai vào ngân hàng thật chỉ để chụp ảnh là thêm dữ liệu bịa vào nơi anh
  đang dùng thật. Chốt ở `assign.test.tsx`, nơi dựng ba bài của hai môn cộng một bài không môn và khẳng định
  đúng ba tiêu đề theo thứ tự `["Toán", "Vật lý", "Chưa rõ môn"]`.
- **Mục "Đã làm"** vẫn chưa có ảnh: lớp thử chưa em nào nộp bài, nên mục ấy không tồn tại trên trang. Nó có ảnh
  khi kịch bản vòng dạy học chạy hết bốn em; cho tới lúc đó, nhóm của mục ấy được chốt ở `assign.test.tsx`.

## Dữ liệu

Bước này **chỉ đọc** — nó dừng trước nút "Bắt đầu", nên không mở bài làm nào. Bài giao mà nó cần là của fixture
(`E2E · bài mẫu` trong `E2E · lớp thử`), dựng một lần và dùng lại: `_paper` tìm theo tiêu đề trước khi tạo, nên
chạy `make e2e-fixture ARGS=--with-exam` nhiều lần không sinh thêm bài giao nào.

**Tên của nó cố tình khác tên đề của vòng dạy học.** Lần đầu tôi đặt trùng `E2E · vòng dạy học`, và đó là một cái
bẫy: kịch bản `teaching-loop` **tự dựng** đề tên ấy qua màn hình, nên hai đề cùng tên sẽ nằm cạnh nhau trong một
tổ chức. Mọi `click td:has-text("E2E · vòng dạy học")` và mọi `[data-testid="open-E2E · vòng dạy học"]` khi ấy
khớp hai phần tử, và Playwright lấy cái **đầu tiên** — bước vẫn xanh, nhưng xanh trên cái đề nó không định nói
tới. Đã xoá đề đặt nhầm ấy (chưa em nào làm) và dựng lại dưới tên riêng.

**Cửa sổ duy nhất làm bước này đỏ vì dữ liệu.** Đề mà `teaching-loop` dựng qua màn hình **không mang môn** (S4 của
vòng ấy chưa chọn Môn), nhưng nhóm là **theo từng mục**, không theo cả trang — nên sau khi vòng chạy xong, bài mẫu
nằm ở "Đang mở" còn đề vòng đã nộp nằm ở "Đã làm", mỗi mục một trạng thái môn, và `h3 = 0` vẫn đúng. Ảnh của lượt
mới nhất cho thấy đúng cảnh ấy: hai mục, không tiêu đề nào. Chỉ có khoảng giữa **giao xong mà chưa nộp** là cả hai
cùng ở "Đang mở" với hai trạng thái môn khác nhau — lúc ấy tiêu đề hiện đúng như thiết kế và bước này sẽ đỏ vì dữ
liệu. Đừng chạy bản này trong lúc vòng dạy học đang dở; hoặc thêm bước chọn Môn vào S4 của vòng khi nào chạy lại.
