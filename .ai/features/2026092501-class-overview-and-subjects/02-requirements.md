---
feature: 2026092501-class-overview-and-subjects
gate: G1
---

# Requirements

## US-01 — Biết một học sinh đã làm gì, lúc nào, mất bao lâu
**Priority:** must

**AC-01** — Lịch sử làm bài trên hồ sơ học sinh
```gherkin
Given một học sinh đã nộp vài bài
When tôi mở hồ sơ em ấy
Then tôi thấy từng lượt làm bài: tên đề, lúc bắt đầu, lúc nộp, số phút từ bắt đầu đến nộp, và điểm
```

**AC-02** — Lượt bị tự nộp vẫn hiện, và nói rõ là tự nộp
```gherkin
Given một lượt làm bài hết giờ và bị hệ thống tự nộp
When tôi xem lịch sử làm bài
Then lượt ấy vẫn nằm trong danh sách và được đánh dấu là tự nộp, không bị giấu đi
```

## US-02 — Nhìn được cả lớp mà không phải rời trang
**Priority:** must

**AC-03** — Tab tổng quan của lớp
```gherkin
Given một lớp đã có bài giao và bài nộp
When tôi mở lớp ấy
Then tôi chọn được giữa "Học sinh" và "Tổng quan", và Tổng quan cho tôi số bài giao, số bài đã nộp,
  điểm trung bình, phổ điểm và những chuyên đề cả lớp yếu nhất
```

**AC-04** — Lớp chưa có bài nộp thì nói thẳng
```gherkin
Given một lớp chưa ai nộp bài
When tôi mở tab Tổng quan
Then màn hình nói rõ chưa có dữ liệu, không hiện một con số 0 trông như đã đo
```

## US-03 — Báo cáo còn đọc được khi trung tâm dạy nhiều môn
**Priority:** must

**AC-05** — Chọn môn, và mặc định không đổi nghĩa
```gherkin
Given trung tâm có nhiều hơn một môn
When tôi mở Báo cáo theo chuyên đề
Then mặc định vẫn là mọi môn như trước, và tôi chọn được một môn để chỉ xem môn ấy
```

**AC-06** — Ở "Mọi môn", mỗi môn một khối
```gherkin
Given báo cáo đang ở "Mọi môn"
When tôi xem cây chuyên đề
Then các mạch kiến thức được nhóm dưới môn của chúng, không nằm phẳng cạnh nhau
```

## US-04 — Menu đi theo trình tự làm việc
**Priority:** should

**AC-07** — Thứ tự nhóm "Lớp & học sinh"
```gherkin
When tôi nhìn thanh điều hướng
Then nhóm "Lớp & học sinh" theo thứ tự Năm học · Cơ cấu trường · Lớp học · Người dùng
```
