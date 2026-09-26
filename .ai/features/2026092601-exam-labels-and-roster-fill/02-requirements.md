---
feature: 2026092601-exam-labels-and-roster-fill
gate: G1
---

# Requirements

## US-01 — Đề thuộc môn nào, khối nào
**Priority:** must

**AC-01** — Đặt Môn và Lớp ngay khi tạo đề
```gherkin
Given tôi mở "Tạo đề"
When tôi nhập tên, chọn môn Toán và khối 11 rồi tạo
Then đề mới mang môn Toán và khối 11
And danh sách đề hiện "11" ở cột Lớp
```

**AC-02** — Sửa được sau, ngay trên trang soạn đề
```gherkin
Given một đề đang không có môn và không có khối
When tôi mở trang soạn đề và chọn môn, chọn khối
Then đề được lưu ngay, không cần nút Lưu riêng
And ma trận của đề chỉ mở chuyên đề của môn vừa chọn
```

**AC-03** — Đổi môn của đề đã có câu hỏi thì nói rõ hệ quả
```gherkin
Given một đề đã có câu hỏi trong đó
When tôi nhìn ô chọn Môn
Then màn hình nói rằng đổi môn chỉ đổi phạm vi ma trận, câu đã có giữ nguyên
```

## US-02 — Biết đã giao đề ôn cá nhân nào, bao giờ, còn hạn không
**Priority:** must

**AC-04** — Ô "Đề ôn cá nhân" nói đủ bốn thứ
```gherkin
Given một học sinh đã được giao một đề ôn cá nhân
When tôi mở tab Tổng quan của lớp
Then ô của em ấy hiện tên đề, ngày giao, hạn nộp và trạng thái
And tên đề mở được báo cáo của bài giao ấy
```

**AC-05** — Quá hạn mà chưa nộp thì nhìn ra ngay
```gherkin
Given hạn của bài giao đã qua và em ấy chưa nộp
When tôi xem ô của em ấy
Then trạng thái nói là quá hạn
And một em đã nộp thì không bị gọi là quá hạn dù hạn đã qua
```

**AC-06** — Giao nhiều đề thì màn hình nói ra là có nhiều
```gherkin
Given một học sinh đã được giao ba đề ôn cá nhân
When tôi xem ô của em ấy
Then ô hiện đề mới nhất và nói còn 2 đề trước đó
```

**AC-07** — Chưa giao lần nào thì nói chưa giao
```gherkin
Given một học sinh chưa được giao đề ôn cá nhân nào
When tôi xem ô của em ấy
Then ô nói là chưa giao, không để trống
```

## US-03 — Rót một lớp mới từ một lớp cũ trong một lần
**Priority:** must

**AC-08** — Chọn lớp cũ, thấy cả danh sách, thêm một lần
```gherkin
Given tôi đang ở lớp mới và mở "Thêm học sinh"
When tôi chuyển sang "Từ lớp cũ" và chọn một lớp
Then mọi học sinh của lớp ấy hiện ra và được tích sẵn
When tôi bấm thêm
Then tất cả các em được tích vào lớp trong một lần gọi
```

**AC-09** — Bỏ tích được từng em
```gherkin
Given danh sách học sinh của lớp nguồn đang tích sẵn
When tôi bỏ tích hai em rồi bấm thêm
Then chỉ những em còn tích được thêm
```

**AC-10** — Em đã ở trong lớp đích thì không thêm lại
```gherkin
Given vài em của lớp nguồn đã có trong lớp đích
When tôi mở danh sách lớp nguồn
Then những em ấy được đánh dấu là đã ở trong lớp và không tích được
```

**AC-11** — Việc chuyển cả năm học vẫn ở chỗ của nó
```gherkin
Given tôi đang ở hộp "Thêm học sinh"
When tôi đọc phần "Từ lớp cũ"
Then màn hình chỉ sang "Chuyển năm học" cho trường hợp chuyển cả năm
```
