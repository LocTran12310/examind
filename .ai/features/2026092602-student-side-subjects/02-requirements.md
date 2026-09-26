---
feature: 2026092602-student-side-subjects
gate: G1
---

# Requirements

## US-01 — Đề ôn tập thuộc một môn
**Priority:** must

**AC-01** — Chọn môn rồi tạo
```gherkin
Given trung tâm dạy hai môn
When tôi bấm "Tạo đề ôn tập"
Then tôi chọn môn trước, mặc định là môn tôi đang yếu nhất
And đề sinh ra mang đúng môn ấy
```

**AC-02** — Một môn thì không hỏi
```gherkin
Given trung tâm chỉ dạy một môn
When tôi bấm "Tạo đề ôn tập"
Then đề được tạo ngay, không hỏi gì
And đề vẫn mang môn duy nhất ấy
```

**AC-03** — Môn đi được tới tận cái đề
```gherkin
Given tôi tạo một đề ôn tập môn Toán
When đề ấy được lưu
Then `exams.subject_id` của nó là môn Toán
And ngân hàng câu hỏi của kế hoạch chỉ gồm câu của môn ấy
```

## US-02 — "Tiến độ của tôi" đọc được khi có nhiều môn
**Priority:** must

**AC-04** — Bộ chọn môn, mặc định mọi môn
```gherkin
Given tôi mở "Tiến độ của tôi"
Then có một bộ chọn môn, mặc định "Mọi môn"
And mọi con số trên trang là của mọi môn, như trước
```

**AC-05** — Chọn một môn thì cả trang theo môn ấy
```gherkin
Given tôi chọn môn Toán
Then mức nắm vững, theo chuyên đề, theo loại câu và lịch sử ôn tập đều chỉ còn Toán
```

**AC-06** — Lịch sử ôn tập gập lại được
```gherkin
Given tôi đã ôn nhiều lần
When tôi mở "Tiến độ của tôi"
Then lịch sử chỉ hiện vài lượt gần nhất và nói còn bao nhiêu lượt nữa
And tôi mở rộng hoặc thu gọn được
```

**AC-07** — Lượt ôn cũ không có môn thì nói thật
```gherkin
Given một lượt ôn tập được tạo trước thay đổi này
When tôi lọc theo một môn
Then lượt ấy không bị gán bừa vào môn nào
```
