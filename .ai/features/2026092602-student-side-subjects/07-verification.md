---
feature: 2026092602-student-side-subjects
environments: [local]
viewports: [desktop, mobile]
---

# Verification — phía học sinh biết môn, và màn hình nhập tài khoản

Bản này kiểm **những gì trung tâm thật cho phép kiểm**, và nói thẳng phần còn lại ở `## Không kiểm ở đây` —
phần ấy lớn hơn thường lệ, vì trung tâm này dạy **đúng một môn**.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert | Env |
|---|---|---|---|---|---|---|
| S1 | Nhập tài khoản: ô kéo thả và link tải file mẫu | `/org/users/import` | `settle 4500` | import-ui | `count [data-testid=file-zone] = 1`; `count input[type=file] = 1`; `count a[href="/mau-nhap-tai-khoan.csv"] = 1`; `text=full_name`; `no-text=Có lỗi xảy ra` | local |

**Bước mở thẳng file mẫu đã bị bỏ, vì trình duyệt không mở được nó**: `.csv` khiến Chromium bắt đầu tải về chứ
không hiện ra trang nào, nên bước ấy đỏ với "Download is starting" — đỏ vì bản chất của định dạng, không vì sản
phẩm. Và điều nó định khẳng định đã được chốt ở chỗ tốt hơn: `import.test.tsx` đọc `href` từ chính DOM, mở file
tại `public/<href>` **trên đĩa** và so hàng tiêu đề với những cột `user_import.py` đọc. Một link trỏ tới đường
dẫn rỗng vẫn là một link trông đúng — nên kiểm phải chạm tới file, và bài test chạm được còn trình duyệt thì
không.

## Không kiểm ở đây

- **Bộ chọn môn trên "Tiến độ của tôi" (AC-04, AC-05) và bước chọn môn khi tạo đề ôn (AC-01)** không dựng được
  ảnh: cả hai **chỉ xuất hiện khi trung tâm có từ hai môn trở lên**, mà `trungtama` dạy đúng một môn. Thêm một
  môn thứ hai vào ngân hàng thật chỉ để chụp một cái ảnh là thêm dữ liệu bịa vào nơi anh đang dùng thật — đúng
  cái giá mà §42 vừa phải trả. Cả ba được chốt ở `practice.test.tsx` và `my-stats.test.tsx`, nơi dựng hai môn
  trong ba dòng.
- **Đề ôn tập mang môn (AC-03)** được chốt ở `test_practice_api.py`: tạo một đề kèm `subject_id` rồi đọc lại
  `exams.subject_id` của chính nó, và tạo một đề không kèm rồi khẳng định nó **không** có môn. Dựng lại trên
  trình duyệt sẽ ghi một lượt làm bài thật vào hồ sơ của một học sinh thật, để đổi lấy một khung hình không cho
  thấy gì hơn.
- **Lịch sử ôn tập gập lại (AC-06)** cần một học sinh đã ôn từ bốn lượt trở lên. Trên trung tâm seed không em
  nào đủ, và bấm tạo đề bốn lần cho một em thật là bốn lượt ôn bịa trong hồ sơ của em ấy. Chốt ở
  `my-stats.test.tsx` với năm lượt dựng sẵn: ba hiện, "Còn 2 lượt nữa", mở ra năm, thu lại ba.
- **Ô kéo thả trông ra sao khi đang kéo** — viền đứt, màu khi rê file vào, vòng focus — không khẳng định được ở
  đâu cả: jsdom không có layout, còn runner thì không mô phỏng được thao tác kéo một file từ hệ điều hành vào.
  S1 khẳng định **cấu trúc** (vùng thả tồn tại, input file vẫn ở đó cho bàn phím và cho điện thoại), phần nhìn
  thì nằm ở tấm ảnh.
