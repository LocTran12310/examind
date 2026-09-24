---
feature: difficulty-at-upload
stories: 4
acceptance_criteria: 6
---

# Requirements

## US-01 — Tách đề xong là có mức độ
**Priority:** must

**AC-01** — Mọi câu đều có mức độ
```gherkin
Given một đề được tải lên và tách xong
When tôi xem các câu của đề ấy
Then mỗi câu đều có một mức độ, và không câu nào để trống
```

**AC-02** — Model dẫn, vị trí lấp
```gherkin
Given model của tổ chức trả lời được cho một số câu
When pipeline gán mức độ
Then những câu model trả lời mang dấu "ai", những câu còn lại mang dấu "auto" theo quy tắc vị trí, và không câu nào bị bỏ trống
```

**AC-03** — Model hỏng thì đề vẫn xong
```gherkin
Given model thiếu, tắt, chậm hoặc trả lời sai định dạng
When pipeline chạy
Then đề vẫn tách xong, mọi câu vẫn có mức độ từ quy tắc vị trí, và cảnh báo được ghi vào nhật ký của đề
```

## US-02 — Không đè lên công của người
**Priority:** must

**AC-04** — `manual` là bất khả xâm phạm
```gherkin
Given một câu đã được một người đặt mức độ
When pipeline hoặc lệnh điền chạy lại trên câu ấy
Then mức độ và dấu vết của nó không đổi
```

## US-03 — Điền cho những câu đã có sẵn
**Priority:** should

**AC-05** — Lệnh điền
```gherkin
Given ngân hàng có những câu chưa có mức độ
When tôi chạy lệnh điền
Then chỉ những câu đang rỗng được điền, chạy lại lần nữa không đổi gì thêm, và lệnh báo lại đã điền bao nhiêu câu bằng tín hiệu nào
```

## US-04 — Nhìn thấy và sửa được
**Priority:** should

**AC-06** — Sửa ngay chỗ đang duyệt
```gherkin
Given một câu trong hàng đợi duyệt
When tôi xem nó
Then tôi thấy mức độ của nó và thấy nó do máy gán hay người đặt, và sửa được ngay tại đó
```
