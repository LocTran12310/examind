---
feature: 2026092601-exam-labels-and-roster-fill
environments: [local]
viewports: [desktop, mobile]
---

# Verification — nhãn của đề, ô ôn cá nhân, và rót lớp

Chạy trên trung tâm thật: 7 lớp · 150 học sinh · 36 đề. Một bước **tạo một đề thật rồi xoá nó ngay trong cùng
lượt chạy** — xem `## Dữ liệu`.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert | Env |
|---|---|---|---|---|---|---|
| S1 | Tạo đề kèm môn và khối, trang soạn đề đọc lại đúng thứ đã chọn | `/org/exams` | `settle 4000; click button:has-text("Tạo đề"); settle 1500; fill [placeholder^="Kiểm tra 15 phút"] = E2E · nhãn đề; click [aria-label="Môn"]; settle 800; click [role=option]:has-text("Toán"); settle 500; click [aria-label="Lớp"]; settle 800; click [role=option]:has-text("Lớp 11"); settle 500; click button:has-text("Tạo và soạn đề"); settle 4500; scroll [id=mon-va-lop]; settle 800` | AC-01, AC-02 | `count [aria-label="Môn của đề"]:has-text("Toán") = 1`; `count [aria-label="Lớp của đề"]:has-text("Lớp 11") = 1`; `text=Ma trận đề chỉ mở chuyên đề của môn này`; `no-text=Có lỗi xảy ra` | local |
| S2 | Cột "Lớp" của danh sách có số | `/org/exams` | `settle 4000; fill [aria-label="Lọc Đề"] = E2E · nhãn đề; settle 3000` | AC-01 | `count tbody tr:has-text("E2E") = 1`; `count tbody tr:has-text("E2E"):has-text("11") = 1`; `no-text=Có lỗi xảy ra` | local |
| S3 | Dọn đúng đề vừa tạo | `/org/exams` | `settle 4000; fill [aria-label="Lọc Đề"] = E2E · nhãn đề; settle 2500; click tbody [aria-label="Chọn dòng"]; settle 800; click button:has-text("Xóa"); settle 1200; click [role=alertdialog] button:has-text("Xóa"); settle 2500` | AC-01 | `count tbody tr:has-text("E2E") = 0`; `no-text=Có lỗi xảy ra` | local |
| S4 | Ô đề ôn cá nhân nói đề nào, giao bao giờ, hạn bao giờ | `/org/classes` | `settle 4000; click td:has-text("12A1"); settle 2500; click a:has-text("Mở trang lớp"); settle 5000; scroll [data-testid=ov-hs001]; settle 1000` | AC-04 | `count [data-testid=ov-hs001] a[href^="/org/assignments/"] = 1`; `count [data-testid=ov-hs001]:has-text("giao ") = 1`; `count [data-testid=ov-hs001]:has-text("hạn ") = 1`; `no-text=chưa giao` | local |
| S5 | Rót lớp mới: chọn lớp cũ, cả lớp tích sẵn | `/org/classes` | `settle 4000; click [aria-label="Chọn năm học"]; settle 1000; click [role=option]:has-text("2027-2028"); settle 3000; click td:has-text("12A99"); settle 2500; click a:has-text("Mở trang lớp"); settle 4500; click [role=tab]:has-text("Học sinh"); settle 2500; click button:has-text("Thêm học sinh"); settle 2500; click [data-testid=source-classes] button:has-text("11A1"); settle 3000` | AC-08, AC-11 | `count [data-testid=source-students] [role=checkbox][data-state=checked] = 25`; `text=Thêm 25 học sinh`; `count a:has-text("Chuyển năm học") = 1`; `no-text=Có lỗi xảy ra` | local |

**Mọi khẳng định của S4 đều bám vào chính ô ấy**, không vào "trang có chữ nào". Bản đầu viết `text=Đề ôn cá
nhân` và nó xanh — nhưng xanh nhờ cái **nút "Giao đề ôn cá nhân"** ở góc trên, đúng loại ô xanh vô nghĩa mà file
này đã ghi hai lần: một khẳng định thoả được ở chỗ khác trên trang thì không nói gì về ô đang kiểm.

**S2 và S3 tách đôi, và đó là một lỗi đã phải sửa.** Bản đầu gộp "xem cột Lớp" với "xoá đề đi" vào một bước:
khẳng định xanh, nhưng ảnh chụp lấy **sau** khi xoá, nên nó cho thấy một bảng rỗng — không thấy cái ô `11` mà
bước tự nhận là đang chứng minh. Đúng câu trong `AGENTS.md`: *một khẳng định thoả được không phải là một tấm ảnh
có ích*. Giờ S2 nhìn thấy hàng ấy còn S3 mới dọn.

Khẳng định của S2 bám vào **chính hàng của đề vừa tạo**, không vào "trang có chữ 11": trước bản sửa cột Lớp
trống ở **mọi** dòng, nên một hàng vừa chứa `E2E` vừa chứa `11` phân biệt được hai bản dựng.

**S5 đổi năm học ở thanh trên trước khi tìm lớp.** Danh sách lớp bám theo năm đang chọn ở header, nên một lớp
của năm sau **không có** trên trang khi header còn ở năm này — bước đầu viết thiếu chỗ ấy và đỏ với "không tìm
thấy 12A99" trong khi lớp vẫn nằm nguyên trong cơ sở dữ liệu. Đúng tình huống anh gặp: lớp mới thuộc năm mới.

**S5 dừng ngay trước nút "Thêm".** Con số **25** là thứ đáng khẳng định: nó nói cả lớp nguồn đã được đọc **và**
mọi em đã được tích sẵn (A-05) — bản dựng nào bỏ sót một em sẽ ra 24. Việc bấm thêm thật thì không chạy ở đây,
vì nó ghi 25 dòng vào một lớp thật và lấy lại phải xoá từng em qua hai trang bảng. Một lời gọi duy nhất cho cả
lớp được chốt ở `classes.test.tsx`, nơi đếm được số lần gọi `POST /classes/{id}/members`.

## Không kiểm ở đây

- **AC-12 (bỏ trống lại được môn/khối) không có bước.** Nó là một lỗi ở tầng máy chủ — `PATCH {grade: null}` từng
  là no-op im lặng — và bằng chứng đúng của nó là `test_exams_api.py`, **đã được chứng minh là đỏ trên mã cũ**
  trước khi xanh trên mã mới. Dựng nó trên trình duyệt sẽ phải đặt rồi xoá nhãn của một đề thật, mà cái thấy được
  trên màn hình lại y hệt cái S1 đã thấy.
- **AC-05 (quá hạn), AC-06 (nhiều đề), AC-07 (chưa giao)** không có ảnh: trung tâm seed giao đúng **một** đề ôn
  cá nhân cho mỗi em và hạn của nó chưa qua, nên ba nhánh kia không tồn tại trong dữ liệu. Giao thêm một vòng chỉ
  để chụp ảnh là thêm 150 bài giao bịa vào lớp thật. Cả ba được chốt ở `mastery.test.tsx`, và AC-06 còn được chốt
  ở tầng API (`test_practice_api.py` giao hai vòng rồi khẳng định `total == 2` — đúng chỗ mà đếm sau `limit(1)`
  sẽ trả lời 1).
- **AC-09, AC-10 (bỏ tích, em đã ở trong lớp)** không có bước: cả hai cần một lớp nguồn có em đã nằm sẵn trong
  lớp đích, mà dựng nó nghĩa là ghi vào lớp thật. `classes.test.tsx` dựng đúng tình huống ấy trong ba dòng.
- **AC-03 (câu cảnh báo khi đề đã có câu hỏi)** không có bước riêng: đề vừa tạo ở S1 chưa có câu nào, nên câu ấy
  **cố tình** không hiện. Nó được chốt ở `exam-builder.test.tsx`.

## Dữ liệu

S1 tạo một đề thật tên `E2E · nhãn đề`; S3 xoá đúng nó trong cùng lượt chạy, qua chính nút Xóa của sản phẩm. Hai
viewport nghĩa là hai cặp tạo–xoá khép kín. Một đề chưa ai làm thì xoá được; nếu S1 đỏ, S2 sẽ không tìm thấy hàng
nào để xoá và cũng đỏ, chứ không xoá nhầm đề khác — bộ lọc là tên đề đầy đủ.

S4 và S5 **chỉ đọc**. S5 dừng trước nút "Thêm" nên không có học sinh nào bị xếp vào lớp nào.
