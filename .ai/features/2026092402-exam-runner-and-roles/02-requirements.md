---
feature: exam-runner-and-roles
stories: 4
acceptance_criteria: 7
---

# Requirements

## US-01 — Khung làm bài đứng yên
**Priority:** must

**AC-01** — Bề rộng không đổi theo nội dung
```gherkin
Given một đề có câu trắc nghiệm dài và câu trả lời ngắn
When học sinh chuyển qua lại giữa các câu
Then khung câu hỏi và bảng câu giữ nguyên vị trí và bề rộng
```

## US-02 — Xem được cả đề
**Priority:** must

**AC-02** — Chuyển giữa hai chế độ
```gherkin
Given đang làm bài
When chọn "Toàn đề"
Then mọi câu hiện theo thứ tự kèm ô trả lời, và chọn "Một câu" thì quay lại đúng câu đang làm
```

**AC-03** — Trả lời được ở chế độ toàn đề
```gherkin
Given đang ở chế độ toàn đề
When trả lời một câu bất kỳ
Then câu đó được lưu như ở chế độ một câu, và bảng câu đánh dấu đã làm
```

## US-03 — Giáo viên chạy thử đề đã giao
**Priority:** must

**AC-04** — Mở được đề đã giao
```gherkin
Given một bài đã giao cho lớp
When giáo viên chọn chạy thử
Then đề mở ra đúng màn hình học sinh thấy, không lộ đáp án trước khi nộp
```

**AC-05** — Có điểm mà không ghi gì
```gherkin
Given giáo viên đã trả lời và nộp bản chạy thử
When kết quả hiện ra
Then có điểm và đáp án, và không một attempt, answer_fact hay mastery nào được tạo
```

## US-04 — Vai trò lồng nhau
**Priority:** must

**AC-06** — Điều hướng lồng nhau
```gherkin
Given đăng nhập bằng giáo viên hoặc quản trị
When xem thanh điều hướng
Then có đủ mục của học sinh, cộng phần của vai trò mình; quản trị có thêm phần của giáo viên
```

**AC-07** — Endpoint phía học sinh nhận nhân viên
```gherkin
Given một giáo viên hoặc quản trị
When gọi các endpoint phía học sinh của chính mình
Then được trả lời như một người dùng bình thường, không phải 403
```
