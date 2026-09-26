---
feature: owner-walk-2
environments: [local]
viewports: [desktop, mobile]
---

# Verification — môn của đề, ô tìm học sinh, và trang chuyển năm gập lại

Ba chỗ sửa rời nhau từ lần anh đi tiếp một vòng. Chạy trên trung tâm thật: 7 lớp · 150 học sinh · 36 đề.
**Không bước nào ghi vào dữ liệu** — cả ba chỉ đọc và dừng trước nút cuối.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert | Env |
|---|---|---|---|---|---|---|
| S1 | Đề chia tab theo môn, mỗi tab mang số của nó | `/org/exams` | `settle 5000; click [role=tab]:has-text("Toán"); settle 3000` | subject-tabs | `count [role=tablist][aria-label="Môn học"] = 1`; `count [role=tab] = 2`; `count [role=tab][data-state=active]:has-text("Toán") = 1`; `count th:has-text("Môn") = 1`; `count tbody tr:first-child:has-text("Toán") = 1`; `no-text=Có lỗi xảy ra` | local |
| S2 | Thêm học sinh: bảng chờ có dòng nhập, gõ tên là vào danh sách | `/org/classes` | `settle 4000; click td:has-text("12A1"); settle 2500; click a:has-text("Mở trang lớp"); settle 4500; click [role=tab]:has-text("Học sinh"); settle 2500; click button:has-text("Thêm học sinh"); settle 2500; fill [aria-label="Tìm học sinh để thêm"] = Học sinh 101; settle 2500; click [data-testid=student-suggestions] li:has-text("hs101"); settle 2000` | staged-rows | `count [data-testid=staged-students] tbody tr:has-text("hs101") = 1`; `text=Thêm 1 học sinh`; `count [role=dialog] [role=tab] = 0`; `text=Chuyển năm học`; `no-text=Có lỗi xảy ra` | local |
| S3 | Trang chuyển năm gập lại: mỗi lớp một dòng, không phải 900 dòng | `/org/school-years` | `settle 4000; click tr:has-text("2026-2027") [aria-label="Chọn dòng"]; settle 1500; click button:has-text("Chuyển năm học"); settle 6000` | folded-plan | `count [data-testid^=plan-] = 6`; `count [data-testid^=summary-] = 6`; `count [aria-label^="Năm mới của"] = 0`; `no-text=Có lỗi xảy ra` | local |
| S4 | Bung một lớp thì thấy học sinh của đúng lớp ấy | `/org/school-years` | `settle 4000; click tr:has-text("2026-2027") [aria-label="Chọn dòng"]; settle 1500; click button:has-text("Chuyển năm học"); settle 6000; click [data-testid=plan-11A1] button:has-text("Lớp 11A1"); settle 2500` | folded-plan | `count [data-testid=plan-11A1] [aria-label^="Năm mới của"] = 25`; `count [aria-label^="Năm mới của"] = 25`; `no-text=Có lỗi xảy ra` | local |
| S5 | Nút chọn mở hộp thoại thứ hai: bảng lớp cũ, mở lớp ra thấy học sinh | `/org/classes` | `settle 4000; click td:has-text("12A1"); settle 2500; click a:has-text("Mở trang lớp"); settle 4500; click [role=tab]:has-text("Học sinh"); settle 2500; click button:has-text("Thêm học sinh"); settle 2500; click [aria-label="Chọn học sinh từ lớp khác"]; settle 2500; click [aria-label="Xem học sinh lớp 11A1"]; settle 3000` | picker-dialog | `count [role=dialog] = 2`; `count [data-testid=source-classes] = 1`; `count [aria-label^="Chọn lớp "] = 6`; `count [aria-label="Chọn Học sinh 101"] = 1`; `no-text=Có lỗi xảy ra` | local |
| S6 | Một phím Escape là đóng hộp thoại | `/org/classes` | `settle 4000; click td:has-text("12A1"); settle 2500; click a:has-text("Mở trang lớp"); settle 4500; click [role=tab]:has-text("Học sinh"); settle 2500; click button:has-text("Thêm học sinh"); settle 2500; press Escape; settle 1500` | escape-once | `count [role=dialog] = 0`; `count [data-testid=source-classes] = 0`; `no-text=Có lỗi xảy ra` | local |
| S7 | Chi tiết lớp: thanh công cụ, tiêu đề và phân trang đứng yên khi cuộn danh sách | `/org/classes` | `settle 4500; click td:has-text("12A1"); settle 4000; scroll section[aria-label="Chi tiết"] tbody tr:last-child; settle 1500` | bounded-detail | `count section[aria-label="Chi tiết"] [data-slot=data-table] = 1`; `count section[aria-label="Chi tiết"] button:has-text("Thêm học sinh") = 1`; `count section[aria-label="Chi tiết"] th:has-text("Tên đăng nhập") = 1`; `count section[aria-label="Chi tiết"] [data-slot=data-table]:has-text("kết quả") = 1`; `no-text=Có lỗi xảy ra` | local |
| S8 | Cơ cấu trường: bảng học sinh của một lớp giữ thanh công cụ, tiêu đề và phân trang | `/org/structure` | `settle 5000; click nav[aria-label="Cơ cấu trường"] button:has-text("12A2"); settle 4500; scroll tbody tr:last-child; settle 1500` | bounded-structure | `count [data-slot=data-table] = 1`; `count [data-slot=data-table] button:has-text("Thêm học sinh") = 1`; `count [data-slot=data-table] th:has-text("Tên đăng nhập") = 1`; `count [data-slot=data-table]:has-text("kết quả") = 1`; `no-text=Có lỗi xảy ra` | local |

**S2 khẳng định `count [role=dialog] [role=tab] = 0`** — hộp thoại không còn tab nào. Đó là khẳng định phân biệt được hai bản
dựng: bản trước có đúng hai tab ở chỗ này. Và `count [aria-label^="Chọn lớp "] = 6` là **mọi lớp khác của tổ
chức** (7 lớp trừ chính lớp đang mở), gồm cả lớp của năm học khác.

**S5 khẳng định `count [role=dialog] = 2`**: hộp chọn là hộp thoại thứ hai chồng lên hộp danh sách chờ, đúng như
anh yêu cầu — không phải thay nội dung hộp đang mở như bản tôi làm lần trước. `count [aria-label^="Chọn lớp "] = 6`
là **mọi lớp khác của tổ chức** (7 lớp trừ chính lớp đang mở), gồm cả lớp của năm học khác.

**S3 khẳng định `count [aria-label^="Năm mới của"] = 0`** — không một ô chọn học sinh nào trong DOM khi mọi lớp
còn gập. Đó là khẳng định phân biệt được hai bản dựng: bản cũ có **150** ô ấy ngay khi trang mở. Và S4 khẳng
định con số **25** ở cả trong thẻ 11A1 lẫn trên toàn trang — bung một lớp không bung lớp khác.

**S1 khẳng định đúng hai tab**, và đó là con số thật của trung tâm này: "Tất cả" và "Toán". **"Chưa phân môn"
cố tình không có** vì không còn đề nào thiếu môn — một tab rỗng là một tab không ai bấm. Không khẳng định "lọc
xong bảng ngắn đi": trung tâm dạy đúng một môn nên chọn Toán **không làm bảng ngắn đi**, và một khẳng định như
thế sẽ xanh giả. Thứ phân biệt được hai bản dựng là **cái tablist tồn tại** và tab đang chọn là Toán.

## Không kiểm ở đây

- **Lọc ra một môn khác** (AC thật của bộ lọc) không kiểm được trên trung tâm này: ngân hàng có đúng một môn, nên
  mọi đề đều là Toán và không có trạng thái thứ hai để so. Chốt ở `exams.test.tsx`, nơi dựng hai môn trong ba
  dòng và khẳng định `filters.subject_id` đi đúng vào thân yêu cầu.
- **Thêm học sinh thật từ bảng tìm rộng** không chạy: nó ghi vào một lớp thật. S2 dừng ở chỗ bảng đã mở với bộ
  lọc và "Chọn tất cả"; việc tích rồi thêm trong **một** lời gọi chốt ở `classes.test.tsx`, nơi đếm được số lần
  gọi `POST /classes/{id}/members`.
- **Bấm "Xác nhận chuyển năm"** không chạy, và sẽ không bao giờ chạy trong một bản kiểm chứng: nó chuyển 150 học
  sinh sang năm học mới và không có nút hoàn tác nào.
