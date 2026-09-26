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
| S1 | Danh sách đề nói môn của từng đề, và lọc được theo môn | `/org/exams` | `settle 4500; click [aria-label="Lọc Môn"]; settle 1200; click [role=option]:has-text("Toán"); settle 3000` | subject-column | `count th:has-text("Môn") = 1`; `count tbody tr:first-child:has-text("Toán") = 1`; `count tbody tr = 20`; `no-text=Có lỗi xảy ra` | local |
| S2 | Ô thêm học sinh có nút mở bảng tìm rộng | `/org/classes` | `settle 4000; click td:has-text("12A1"); settle 2500; click a:has-text("Mở trang lớp"); settle 4500; click [role=tab]:has-text("Học sinh"); settle 2500; click button:has-text("Thêm học sinh"); settle 2000; click [role=tab]:has-text("Tìm từng em"); settle 1200; click [aria-label="Tìm nâng cao"]; settle 3000` | wide-search | `count [data-testid=wide-results] = 1`; `count [aria-label="Lọc theo lớp"] = 1`; `text=Chọn tất cả`; `text=Còn 100 kết quả nữa`; `no-text=Có lỗi xảy ra` | local |
| S3 | Trang chuyển năm gập lại: mỗi lớp một dòng, không phải 900 dòng | `/org/school-years` | `settle 4000; click tr:has-text("2026-2027") [aria-label="Chọn dòng"]; settle 1500; click button:has-text("Chuyển năm học"); settle 6000` | folded-plan | `count [data-testid^=plan-] = 6`; `count [data-testid^=summary-] = 6`; `count [aria-label^="Năm mới của"] = 0`; `no-text=Có lỗi xảy ra` | local |
| S4 | Bung một lớp thì thấy học sinh của đúng lớp ấy | `/org/school-years` | `settle 4000; click tr:has-text("2026-2027") [aria-label="Chọn dòng"]; settle 1500; click button:has-text("Chuyển năm học"); settle 6000; click [data-testid=plan-11A1] button:has-text("Lớp 11A1"); settle 2500` | folded-plan | `count [data-testid=plan-11A1] [aria-label^="Năm mới của"] = 25`; `count [aria-label^="Năm mới của"] = 25`; `no-text=Có lỗi xảy ra` | local |

**S3 khẳng định `count [aria-label^="Năm mới của"] = 0`** — không một ô chọn học sinh nào trong DOM khi mọi lớp
còn gập. Đó là khẳng định phân biệt được hai bản dựng: bản cũ có **150** ô ấy ngay khi trang mở. Và S4 khẳng
định con số **25** ở cả trong thẻ 11A1 lẫn trên toàn trang — bung một lớp không bung lớp khác.

**S1 khẳng định `count tbody tr = 20`** vì trung tâm chỉ dạy một môn: lọc theo Toán **không làm bảng ngắn đi**,
nên một khẳng định kiểu "sau khi lọc còn ít dòng hơn" sẽ xanh giả. Thứ kiểm được là cột tồn tại, hàng đầu đọc
"Toán", và trang vẫn đủ 20 dòng của trang một.

## Không kiểm ở đây

- **Lọc ra một môn khác** (AC thật của bộ lọc) không kiểm được trên trung tâm này: ngân hàng có đúng một môn, nên
  mọi đề đều là Toán và không có trạng thái thứ hai để so. Chốt ở `exams.test.tsx`, nơi dựng hai môn trong ba
  dòng và khẳng định `filters.subject_id` đi đúng vào thân yêu cầu.
- **Thêm học sinh thật từ bảng tìm rộng** không chạy: nó ghi vào một lớp thật. S2 dừng ở chỗ bảng đã mở với bộ
  lọc và "Chọn tất cả"; việc tích rồi thêm trong **một** lời gọi chốt ở `classes.test.tsx`, nơi đếm được số lần
  gọi `POST /classes/{id}/members`.
- **Bấm "Xác nhận chuyển năm"** không chạy, và sẽ không bao giờ chạy trong một bản kiểm chứng: nó chuyển 150 học
  sinh sang năm học mới và không có nút hoàn tác nào.
