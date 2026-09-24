---
feature: blueprint-truth
stories: 3
acceptance_criteria: 5
---

# Requirements

## US-01 — Con số nói thật
**Priority:** must

**AC-01** — Số câu theo đúng bộ lọc của dòng
```gherkin
Given một dòng ma trận trên một chuyên đề có 14 câu, trong đó 7 câu Trắc nghiệm
When dòng ấy chọn loại câu Trắc nghiệm
Then con số bên cạnh đọc 7, và bằng đúng số câu lệnh tạo đề lấy được
```

**AC-02** — Đổi bộ lọc thì số đổi theo
```gherkin
Given một dòng đang hiện số câu của nó
When tôi đổi loại câu hoặc mức độ của dòng ấy
Then con số tính lại theo bộ lọc mới, không cần tạo đề mới biết
```

## US-02 — Thiếu câu thì nói vì sao
**Priority:** must

**AC-03** — Lý do thiếu
```gherkin
Given một dòng đòi nhiều câu hơn số nó lấy được
When màn hình báo thiếu
Then nó nói rõ chuyên đề có bao nhiêu câu tất cả và bao nhiêu câu hợp bộ lọc của dòng
```

## US-03 — Không dán nhãn, và nút đọc được
**Priority:** must

**AC-04** — Không còn nhãn xếp hạng
```gherkin
Given màn kết quả bài làm, hồ sơ học sinh và tình hình lớp
When tôi xem các mục theo chuyên đề
Then thứ tự vẫn là cần ôn trước, nhưng không chỗ nào gọi đó là "yếu nhất" hay "cần ôn nhất"
```

**AC-05** — Nút chế độ xem có icon và tooltip
```gherkin
Given màn làm bài
When tôi nhìn nút chuyển chế độ xem
Then mỗi chế độ có icon riêng và một tooltip nói nó làm gì
```
