---
feature: add-student-flow
environments: [local]
viewports: [desktop, mobile]
---

# Verification — đi hết luồng thêm học sinh, kể cả lúc bấm Lưu

Các bản kiểm trước dừng **trước** nút lưu, nên chúng chứng minh được màn hình chứ chưa chứng minh được **việc**.
Bản này đi hết: gõ một em, chọn thêm hai em từ lớp cũ, bấm thêm, xem lớp nhận đủ ba — rồi **tự dọn**.

Lớp đích là **12A99 · 2027-2028**, lớp trống của năm mới. Ba em được thêm vẫn giữ nguyên lớp 11A1 của mình (một
học sinh thuộc được nhiều lớp), nên bước dọn trả mọi thứ về đúng như trước.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert | Env |
|---|---|---|---|---|---|---|
| S1 | Gõ tên vào dòng nhập là vào danh sách chờ | `/org/classes` | `settle 4000; click [aria-label="Chọn năm học"]; settle 1000; click [role=option]:has-text("2027-2028"); settle 3000; click td:has-text("12A99"); settle 2500; click a:has-text("Mở trang lớp"); settle 4500; click [role=tab]:has-text("Học sinh"); settle 2500; click button:has-text("Thêm học sinh"); settle 2500; fill [aria-label="Tìm học sinh để thêm"] = Học sinh 101; settle 2500; click [data-testid=student-suggestions] li:has-text("hs101"); settle 1500` | staging | `count [data-testid=staged-students] tbody tr:has-text("hs101") = 1`; `text=Lớp 11A1`; `text=Thêm 1 học sinh`; `no-text=Có lỗi xảy ra` | local |
| S2 | Hộp chọn đưa thêm hai em vào cùng danh sách chờ, chưa lưu gì | `/org/classes` | `settle 4000; click [aria-label="Chọn năm học"]; settle 1000; click [role=option]:has-text("2027-2028"); settle 3000; click td:has-text("12A99"); settle 2500; click a:has-text("Mở trang lớp"); settle 4500; click [role=tab]:has-text("Học sinh"); settle 2500; click button:has-text("Thêm học sinh"); settle 2500; fill [aria-label="Tìm học sinh để thêm"] = Học sinh 101; settle 2500; click [data-testid=student-suggestions] li:has-text("hs101"); settle 1200; click [aria-label="Chọn học sinh từ lớp khác"]; settle 2500; click [aria-label="Xem học sinh lớp 11A1"]; settle 2500; click [aria-label="Chọn Học sinh 102"]; settle 600; click [aria-label="Chọn Học sinh 103"]; settle 600; click button:has-text("Chọn 2 học sinh"); settle 2000` | staging | `count [role=dialog] = 1`; `count [data-testid=staged-students] tbody tr = 4`; `text=Thêm 3 học sinh`; `count table:has-text("Lớp chưa có học sinh") = 1`; `no-text=Có lỗi xảy ra` | local |
| S3 | Bấm thêm: lớp nhận đủ ba em | `/org/classes` | `settle 4000; click [aria-label="Chọn năm học"]; settle 1000; click [role=option]:has-text("2027-2028"); settle 3000; click td:has-text("12A99"); settle 2500; click a:has-text("Mở trang lớp"); settle 4500; click [role=tab]:has-text("Học sinh"); settle 2500; click button:has-text("Thêm học sinh"); settle 2500; fill [aria-label="Tìm học sinh để thêm"] = Học sinh 101; settle 2500; click [data-testid=student-suggestions] li:has-text("hs101"); settle 1200; click [aria-label="Chọn học sinh từ lớp khác"]; settle 2500; click [aria-label="Xem học sinh lớp 11A1"]; settle 2500; click [aria-label="Chọn Học sinh 102"]; settle 600; click [aria-label="Chọn Học sinh 103"]; settle 600; click button:has-text("Chọn 2 học sinh"); settle 1500; click button:has-text("Thêm 3 học sinh"); settle 4000` | saving | `text=Đã thêm 3 học sinh vào lớp`; `count [role=dialog] = 0`; `count tbody tr:has-text("hs101") = 1`; `count tbody tr:has-text("hs102") = 1`; `count tbody tr:has-text("hs103") = 1`; `no-text=Lớp chưa có học sinh` | local |
| S4 | Dọn: bỏ đúng ba em ấy ra khỏi lớp | `/org/classes` | `settle 4000; click [aria-label="Chọn năm học"]; settle 1000; click [role=option]:has-text("2027-2028"); settle 3000; click td:has-text("12A99"); settle 2500; click a:has-text("Mở trang lớp"); settle 4500; click [role=tab]:has-text("Học sinh"); settle 3000; click thead [aria-label="Chọn tất cả"]; settle 1200; click button:has-text("Xóa"); settle 1500; click [role=alertdialog] button:has-text("Xóa"); settle 3500` | cleanup | `text=Lớp chưa có học sinh`; `no-text=hs101`; `no-text=Có lỗi xảy ra` | local |

**S2 khẳng định `count [role=dialog] = 1`**: hộp chọn đã đóng sau khi bấm "Chọn", còn hộp danh sách chờ vẫn mở.
Và **`count table:has-text("Lớp chưa có học sinh") = 1`** là chỗ chứng minh *chưa lưu gì*: bảng học sinh của lớp
nằm ngay phía sau hộp thoại và vẫn đang rỗng. Trên bản trước bản này, bấm chọn là **ghi thẳng vào lớp** — nên
khẳng định ấy phân biệt được hai bản dựng, không chỉ mô tả bản hiện tại.

**`count [data-testid=staged-students] tbody tr = 4`** là ba hàng học sinh **cộng dòng nhập** — dòng nhập cũng là
một hàng của bảng ấy, đúng như anh mô tả ("table với row input").

## Dữ liệu

S3 **ghi thật**: ba học sinh vào lớp 12A99. S4 lấy lại trong cùng lượt chạy, qua chính nút Xóa của sản phẩm. Hai
viewport nghĩa là hai vòng thêm–xoá khép kín. Ba em ấy vẫn ở nguyên lớp 11A1 từ đầu đến cuối — một học sinh
thuộc được nhiều lớp, nên vòng này không đụng gì tới lớp cũ của họ.

Nếu S3 đỏ thì S4 sẽ không có gì để xoá và cũng đỏ (`text=Lớp chưa có học sinh` vốn đã đúng), chứ không xoá nhầm
học sinh của lớp khác: nó chỉ chọn cả trang của **lớp 12A99** rồi bấm Xóa.
