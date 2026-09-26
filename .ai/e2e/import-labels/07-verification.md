---
feature: import-labels
environments: [local]
viewports: [desktop, mobile]
---

# Verification — màn nhập tài khoản nói cùng một thứ tiếng với file xuất ra

Anh mở file xuất ra thấy `Họ tên · Tên đăng nhập · Vai trò · Lớp` và `Học sinh · Giáo viên`, mở file mẫu để nhập
lại thì thấy `full_name · username · role · class` và `student · teacher`. Hai bộ chữ cho một việc. Bản này kiểm
cái nhìn thấy được: màn nhập giờ gọi cột bằng đúng tên mà file xuất ra dùng.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert | Env |
|---|---|---|---|---|---|---|
| S1 | Gợi ý cột bằng tên tiếng Việt, và tên tiếng Anh nói rõ là vẫn nhận | `/org/users/import` | `settle 4500` | one-vocabulary | `text=Cột: Họ tên`; `text=Tên cột tiếng Anh`; `count a[href="/mau-nhap-tai-khoan.csv"] = 1`; `count [data-testid=file-zone] = 1`; `no-text=Có lỗi xảy ra` | local |

**`text=Cột: Họ tên` phân biệt được hai bản dựng**: bản trước mở đầu bằng `Cột: full_name`. Và
`text=Tên cột tiếng Anh` khẳng định phần thứ hai của việc này — nhận diện chứ không cấm: một file do script viết
ra với tên cột tiếng Anh vẫn đọc được, và câu ấy nói cho người dùng biết điều đó.

## Không kiểm ở đây

- **Nội dung file xuất ra** không dựng được ảnh: trình duyệt không mở `.csv`, nó tải về — bài học đã ghi ở
  `2026092602`. Chốt ở `users.test.tsx`, nơi bấm đúng nút "Xuất khẩu", đọc chính cái Blob đi ra, so hàng tiêu đề
  với **file mẫu đọc từ đĩa**, và khẳng định hai lớp của một em đi ra dưới dạng `10A1; 11A2`. Một khẳng định trên
  màn hình không chạm được tới byte nào của file; bài test thì chạm được.
- **Đọc ngược lại file ấy** chốt ở `test_import.py::test_a_file_the_export_wrote_reads_back`: dựng đúng hàng tiêu
  đề của file xuất (kể cả cột Email mà bộ nhập không dùng), ba vai trò viết bằng nhãn tiếng Việt, một ô hai lớp —
  rồi khẳng định tạo ra **hai** lớp chứ không phải một lớp tên `12X1; 12X2`.
