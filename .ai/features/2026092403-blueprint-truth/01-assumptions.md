---
feature: blueprint-truth
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | Con số cạnh một dòng ma trận là số câu **dòng ấy** lấy được — tức đã áp chuyên đề, loại câu và mức độ của chính nó — và đổi theo khi đổi bộ lọc | high | yes | Soạn đề | confirmed | Loc Tran nêu trong chat (2026-09-24); đây là nguyên nhân của "14 câu nhưng chỉ tạo được 7" |
| A-02 | Con số ấy lấy từ đúng phép lọc mà lệnh tạo đề dùng (`status: usable` + chuyên đề + loại + mức độ), không phải một phép đếm song song | high | yes | Soạn đề | confirmed | Accepted under blanket pre-approval. Hai phép đếm khác nhau sẽ lệch, và lần lệch đầu tiên chính là lỗi này |
| A-03 | Khi một dòng không đủ câu, màn hình nói rõ đang thiếu vì đâu — chuyên đề hết câu, hay bộ lọc của dòng cắt mất | high | no | Soạn đề | confirmed | Accepted under blanket pre-approval; "thiếu 3 câu" một mình là thứ Loc Tran đã nói là không hiểu |
| A-04 | Không màn hình nào dán nhãn xếp hạng lên chuyên đề của một người học ("yếu nhất", "giỏi nhất", "cần ôn nhất") | high | no | Kết quả, hồ sơ | confirmed | Loc Tran nêu trong chat (2026-09-24): "rất dễ rơi vào bẫy tâm lý". Thứ tự sắp xếp giữ nguyên — chỉ bỏ cách gọi tên |
| A-05 | Nút "Một câu / Toàn đề" có icon; chữ giữ lại hay không là tuỳ chỗ, nhưng phải có tooltip | medium | no | Màn làm bài | confirmed | Accepted under blanket pre-approval theo yêu cầu "thêm icon hoặc chuyển sang Icon rồi thêm tooltip" |
