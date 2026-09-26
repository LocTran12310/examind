---
feature: ui-followups
environments: [local]
viewports: [desktop, mobile]
---

# Verification — năm chỗ sửa sau lần anh đi một vòng (2026-09-26)

Không phải một feature AI-DLC: năm chỗ sửa rời nhau, đến từ ảnh chụp anh gửi. Bản này chạy trên **trung tâm
thật**, và có một bước **ghi vào dữ liệu thật rồi tự lấy lại** — xem `## Dữ liệu` ở cuối.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert | Env |
|---|---|---|---|---|---|---|
| S1 | Cột "Tiến độ" sắp xếp được: đề dở dang nhất lên đầu | `/org/review` | `settle 4500; click th:has-text("Tiến độ") button; settle 3000` | sort-progress | `count th[aria-sort="ascending"] = 1`; `count tbody tr:first-child:has-text("HKHTN") = 1`; `count tbody tr:first-child:has-text("45%") = 1`; `no-text=Có lỗi xảy ra` | local |
| S2 | Sửa hàng loạt xong thì thanh công cụ thôi đếm | `/org/bank` | `settle 4500; click [aria-label="Chọn câu"]; settle 1200; click button:has-text("Mức độ"); settle 1200; click [role=menuitem]:has-text("Nhận biết"); settle 3000` | clear-selection | `text=Đã đặt mức độ Nhận biết`; `no-text=Đã chọn`; `no-text=Có lỗi xảy ra` | local |
| S3 | Lấy lại đúng câu vừa sửa | `/org/bank` | `settle 4500; click button:has-text("Thay đổi gần đây"); settle 2500; click button:has-text("Hoàn tác"); settle 3000` | clear-selection | `text=Đã hoàn tác`; `no-text=Có lỗi xảy ra` | local |
| S4 | Bảng câu bám lại khi cuộn xuống | `/org/assignments/52124988-53e4-4fd3-a21d-9dae999e55b0/trial` | `settle 5000; click [role=radio]:has-text("Toàn đề"); settle 2500; click [aria-label="Câu 15"]; settle 3000` | sticky-navigator | `count [data-testid=navigator] = 1`; `no-text=Có lỗi xảy ra` | local |
| S5 | Ma trận nói phần đến từ loại câu, và dòng "mọi loại" đọc được | `/org/exams` | `settle 4000; fill [aria-label="Lọc Đề"] = Chuyên đề Thống kê và Xác suất · 11A2; settle 3000; click button:has-text("Chuyên đề Thống kê và Xác suất · 11A2"); settle 3500; click a:has-text("Soạn đề & giao bài"); settle 4500; scroll [data-testid=blueprint]; settle 1000` | parts-from-type | `count [data-testid=blueprint-parts] = 1`; `text=Trắc nghiệm → Phần I`; `count [aria-label="Loại câu"]:has-text("Mọi loại") = 1` | local |
| S6 | Lỗi hiện ở góc phải dưới, nơi mắt đang nhìn | `/org/exams/853b31d2-d964-4d51-a880-b4b0073df858` | `settle 5000; scroll button:has-text("Tạo đề theo ma trận"); settle 800; click button:has-text("Tạo đề theo ma trận"); settle 2500` | error-toast | `count [data-sonner-toast] = 1`; `text=Đề đã có học sinh làm`; `count [data-testid=blueprint] ~ [role=alert] = 0` | local |

**S1 khẳng định hàng đầu tiên, không khẳng định "có chữ 45%".** Trước khi sắp xếp, trang đã có sẵn cả 95% lẫn
45% trên màn hình, nên một khẳng định `text=45%` đúng ở cả hai trạng thái và không chứng minh gì. Thứ đổi là
**thứ tự**: đề dở dang nhất đi từ gần cuối lên hàng đầu.

**Và nó khẳng định `HKHTN`, không phải `CHUYÊN ĐHKHTN`** — không phải để cho ngắn. Bản đầu viết đủ chữ và đỏ với
`found 0` trong khi ảnh chụp hiện đúng dòng ấy ở hàng đầu. Lý do: tên tệp đến từ macOS nên nằm trong cơ sở dữ
liệu ở dạng **NFD** (`CHUYÊN` là `C H U Y E U+0302 N`), còn chuỗi tôi gõ vào file này là NFC; Playwright so khớp
chữ **không chuẩn hoá Unicode**, nên hai chuỗi trông giống hệt nhau trên màn hình mà không khớp nhau. Mọi khẳng
định trên một **tên tài liệu** đều dính bẫy này; chữ do chính ứng dụng viết (nhãn, câu thông báo) thì không, vì
nó là NFC trong mã nguồn.

**S6 không ghi gì.** Đề `853b31d2` đã có **25 lượt làm**, nên máy chủ từ chối mọi thay đổi trước khi chạm vào
đâu (`guard_edit`) — đúng cái 409 mà bước này cần. Và nó chọn đúng nút nằm **dưới màn hình**: chỗ lỗi cũ in ở
đầu trang là chỗ không ai nhìn sau khi đã cuộn tới đây.

## Không kiểm bằng khẳng định

- **Lỗi hiện bằng toast (S6) không thể xanh ở đây.** Ảnh chụp cho thấy đúng thứ cần thấy — toast đỏ ở góc phải
  dưới, đầu trang sạch — nhưng bước vẫn đỏ, vì một lần từ chối của máy chủ là một phản hồi không-2xx và trình
  duyệt ghi `console.error` cho nó, mà `console_errors` là failure signal của repo. Đó là **quyết định của chủ
  dự án ngày 2026-09-24**: giữ tín hiệu và chấp nhận các bước đỏ kiểu này, vì bỏ nó cũng bỏ luôn `pageerror` —
  runner chỉ đăng ký `pageerror` khi `console_errors` bật — tức mọi feature mất khả năng bắt ngoại lệ chưa bắt,
  để cứu vài bước. Bước được **giữ lại đỏ** chứ không xoá: xoá đi sẽ có một lượt chạy xanh chứng minh ít hơn.
  Hành vi được chốt ở `exam-builder.test.tsx`, nơi khẳng định được cả rằng chữ ấy nằm trong `[data-sonner-toast]`.
- **Bảng câu bám màn hình (S4) không có khẳng định nào chứng minh được.** Bảng khẳng định chỉ có `count`,
  `text=` và `no-text=`, mà `text=` của Playwright vẫn đúng cho một phần tử **nằm ngoài khung nhìn** — nên
  "Bảng câu còn trên màn hình" viết thành khẳng định sẽ xanh cả trước lẫn sau khi sửa. Bước này vì vậy khẳng
  định phần tử **tồn tại** và cuộn xuống cuối đề; thứ chứng minh là **tấm ảnh**, và nó phải cho thấy bảng câu
  nằm cạnh câu hỏi cuối. Một bước không phân biệt được hai bản dựng thì bằng chứng của nó là ảnh, không phải ô
  xanh — và nói ra điều đó là phần bắt buộc.
- **Ở 390px bảng câu cố tình KHÔNG bám** (`md:sticky`): dưới `md` nó nằm **dưới** các câu hỏi, ghim ở đó là phủ
  lên chính bài đang làm. Ảnh mobile của S4 vì vậy cho thấy nó trôi đi, và đó là đúng.

## Dữ liệu

S2 đặt mức độ cho **một** câu trong ngân hàng thật; S3 hoàn tác ngay trong cùng lượt chạy, qua chính "Thay đổi
gần đây" của sản phẩm. Hoàn tác đi qua danh sách chứ không qua nút trong toast, vì runner nạp lại trang cho mỗi
bước và toast không sống qua lần nạp ấy — bài học đã trả giá ở `.ai/features/2026092305-bulk-safety`.

Chạy ở hai viewport nghĩa là S2/S3 chạy **hai lần**, mỗi lần một cặp sửa–hoàn tác khép kín.

Và thực tế còn nhẹ hơn thế: câu đầu ngân hàng **vốn đã là "Nhận biết"**, nên phần lớn lượt chạy ghi một lượt sửa
**không đổi trường nào** — cột "Đã đổi" trong "Thay đổi gần đây" hiện `—`. Chỉ một lượt (02:19) thật sự đổi mức
độ của một câu, và nó cũng đã được hoàn tác. Đừng dựa vào điều đó: nó đúng vì thứ tự mặc định của ngân hàng hôm
nay, không phải vì bước kiểm được thiết kế thế — bước vẫn phải tự hoàn tác.
