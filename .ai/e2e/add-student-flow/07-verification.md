---
feature: add-student-flow
environments: [local]
viewports: [desktop, mobile]
---

# Verification — đi hết luồng thêm học sinh, kể cả lúc bấm Lưu

Các bản kiểm trước dừng **trước** nút lưu, nên chúng chứng minh được màn hình chứ chưa chứng minh được **việc**.
Bản này đi hết: dựng một lớp trống của riêng nó, gõ một em, chọn thêm hai em từ lớp cũ, bấm thêm, xem lớp nhận
đủ ba — rồi **xoá luôn cái lớp ấy**.

**Vì sao lớp phải là của riêng bản kiểm.** Bản đầu mượn `12A99`, lớp trống anh tự tạo. Rồi anh dùng nó thật —
thêm `hs050` vào — và bản kiểm đỏ ở đúng chỗ nó khẳng định "lớp chưa có học sinh", còn bước dọn thì không dám
xoá cả trang vì trong đó có em của anh. Ba em của lượt chạy hỏng ở lại trong lớp cho tới khi tôi gỡ tay. Một bản
kiểm chứng dùng chung dữ liệu với người dùng là một bản kiểm chứng sẽ hỏng vào ngày người dùng động tới nó.

Xoá lớp mang theo mọi bản ghi thành viên của nó (`delete_class`), còn **tài khoản học sinh thì không hề đụng
tới** — các em vẫn ở nguyên lớp cũ của mình, vì một học sinh thuộc được nhiều lớp.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert | Env |
|---|---|---|---|---|---|---|
| S1 | Dựng một lớp trống cho chính bản kiểm này | `/org/classes` | `settle 4500; click button:has-text("Thêm mới"); settle 2000; fill [role=dialog] [placeholder="10A1"] = E2E lớp kiểm; settle 500; click button:has-text("Tạo lớp"); settle 3500; fill [aria-label="Lọc Lớp"] = E2E lớp kiểm; settle 2500` | own-class | `count tbody tr:has-text("E2E lớp kiểm") = 1`; `no-text=Có lỗi xảy ra` | local |
| S2 | Gõ tên vào dòng nhập là vào danh sách chờ, và chưa lưu gì | `/org/classes` | `settle 4500; fill [aria-label="Lọc Lớp"] = E2E lớp kiểm; settle 2500; click td:has-text("E2E lớp kiểm"); settle 3000; click section[aria-label="Chi tiết"] button:has-text("Thêm học sinh"); settle 2500; fill [aria-label="Tìm học sinh để thêm"] = Học sinh 101; settle 2500; click [data-testid=student-suggestions] li:has-text("hs101"); settle 1500` | staging | `count [data-testid=staged-students] tbody tr:has-text("hs101") = 1`; `count [data-testid=staged-students] tbody tr:has-text("Lớp 11A1") = 1`; `text=Thêm 1 học sinh`; `count section[aria-label="Chi tiết"]:has-text("Lớp chưa có học sinh") = 1`; `no-text=Có lỗi xảy ra` | local |
| S3 | Hộp chọn thêm hai em nữa, rồi bấm lưu: lớp nhận đủ ba | `/org/classes` | `settle 4500; fill [aria-label="Lọc Lớp"] = E2E lớp kiểm; settle 2500; click td:has-text("E2E lớp kiểm"); settle 3000; click section[aria-label="Chi tiết"] button:has-text("Thêm học sinh"); settle 2500; fill [aria-label="Tìm học sinh để thêm"] = Học sinh 101; settle 2500; click [data-testid=student-suggestions] li:has-text("hs101"); settle 1200; click [aria-label="Chọn học sinh từ lớp khác"]; settle 2500; click [aria-label="Xem học sinh lớp 11A1"]; settle 2500; click [aria-label="Chọn Học sinh 102"]; settle 600; click [aria-label="Chọn Học sinh 103"]; settle 600; click button:has-text("Chọn 2 học sinh"); settle 1500; click button:has-text("Thêm 3 học sinh"); settle 4000` | saving | `text=Đã thêm 3 học sinh vào lớp`; `count [role=dialog] = 0`; `count section[aria-label="Chi tiết"] tbody tr:has-text("hs101") = 1`; `count section[aria-label="Chi tiết"] tbody tr:has-text("hs102") = 1`; `count section[aria-label="Chi tiết"] tbody tr:has-text("hs103") = 1` | local |
| S4 | Dọn: xoá cái lớp bản kiểm đã dựng | `/org/classes` | `settle 4500; fill [aria-label="Lọc Lớp"] = E2E lớp kiểm; settle 2500; click tbody [aria-label="Chọn dòng"]; settle 1200; click button:has-text("Xóa"); settle 1500; click [role=alertdialog] button:has-text("Xóa"); settle 3500` | cleanup | `count tbody tr:has-text("E2E lớp kiểm") = 0`; `no-text=Có lỗi xảy ra` | local |

**S2 chứng minh "chưa lưu gì" bằng chính bảng phía sau**: mục "Chi tiết" của lớp vừa dựng vẫn đọc "Lớp chưa có
học sinh" trong khi danh sách chờ đã có một em. Trên bản trước bản này, bấm chọn là **ghi thẳng vào lớp** — nên
khẳng định ấy phân biệt được hai bản dựng, không chỉ mô tả bản hiện tại. Nó bám vào `section[aria-label="Chi
tiết"]`, vì mục ấy là chỗ duy nhất câu kia được phép xuất hiện.

**Khẳng định về lớp hiện tại phải bám vào hàng**, không phải `text=Lớp 11A1`: ở bề rộng điện thoại, tên đăng
nhập và lớp hiện tại xuống dòng thứ hai ngay dưới tên, nên **cùng một chuỗi có mặt hai lần trong DOM**, mỗi bản
ẩn ở một bề rộng. `text=` của Playwright lấy phần tử khớp **đầu tiên** rồi đợi nó hiện ra — ở desktop đó lại
đúng là bản dành cho điện thoại, đang `display:none`, nên bước đỏ trong khi màn hình hiện chữ ấy rõ ràng.

## Dữ liệu

Lớp `E2E lớp kiểm` được dựng ở S1 và xoá ở S4, trong cùng một lượt chạy. Hai viewport nghĩa là hai vòng
dựng–xoá khép kín, và desktop xoá xong mới tới lượt mobile dựng. Ba học sinh được thêm vào lớp ấy vẫn ở nguyên
lớp 11A1 của mình từ đầu đến cuối.

Nếu S1 đỏ thì S2–S4 không tìm thấy lớp nào tên ấy và cùng đỏ, chứ không đụng vào lớp khác: mọi bước đều lọc
danh sách theo đúng cái tên ấy trước khi bấm bất cứ thứ gì.
