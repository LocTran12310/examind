---
feature: blank-options
stories: 1
acceptance_criteria: 3
---

# Requirements

## US-01 — Phương án hiện đúng nội dung đã soạn
**Priority:** must

**AC-01** — Số có dấu chấm vẫn là số
```gherkin
Given một phương án có nội dung "9."
When câu hỏi được hiển thị ở bất kỳ màn nào
Then phương án ấy đọc là "9." chứ không phải một ô trống
```

**AC-02** — Công thức và chữ không đổi
```gherkin
Given các phương án chứa công thức, chữ thường, hình ảnh
When câu hỏi được hiển thị
Then chúng hiện đúng như trước, không có gì bị escape lộ ra màn hình
```

**AC-03** — Đề bài và lời giải giữ nguyên
```gherkin
Given một đề bài có danh sách đánh số thật
When câu hỏi được hiển thị
Then danh sách ấy vẫn là danh sách
```
