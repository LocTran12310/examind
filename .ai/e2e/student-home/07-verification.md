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
| S1 | Trang chủ học sinh: các mục còn nguyên, không có tiêu đề môn thừa | `/home` | `settle 5000` | flat-when-one-subject | `text=Đang mở`; `count h3 = 0`; `no-text=Chưa rõ môn`; `no-text=Có lỗi xảy ra` | e2e-hs01 |

**Và phải nói thẳng bước này chứng minh được tới đâu.** Tài khoản `e2e.hs01` vừa dựng lại **chưa được giao bài
nào**, nên ảnh chụp là trạng thái rỗng ("Không có bài nào đang mở"). Với danh sách rỗng thì `count h3 = 0` đúng
một cách tầm thường — nó **không** phân biệt được hai bản dựng. Thứ bước này thật sự chứng minh là hẹp hơn
nhiều, và vẫn đáng có: một học sinh thật đăng nhập được, trang chủ dựng được cho vai học sinh, và vòng lặp nhóm
mới thêm vào **không ném lỗi** trên đường đi.

Muốn nó nói được nhiều hơn thì phải giao cho em ấy một bài thật, tức thêm một bước của vai giáo viên và một bài
giao vào lớp thử. Chưa làm; ghi ra đây để lần sau không ai đọc dòng "2/2" rồi tưởng cái nhóm đã được chụp ảnh.

## Không kiểm ở đây

- **Chính việc nhóm theo môn** (nhiều môn, và bài chưa rõ môn đứng riêng ở cuối) không dựng được ảnh trên trung
  tâm này: nó dạy một môn. Thêm môn thứ hai vào ngân hàng thật chỉ để chụp ảnh là thêm dữ liệu bịa vào nơi anh
  đang dùng thật. Chốt ở `assign.test.tsx`, nơi dựng ba bài của hai môn cộng một bài không môn và khẳng định
  đúng ba tiêu đề theo thứ tự `["Toán", "Vật lý", "Chưa rõ môn"]`.
