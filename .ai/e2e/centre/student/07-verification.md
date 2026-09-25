---
feature: centre-student
environments: [e2e-hs01]
viewports: [desktop]
---

# Phía học sinh — một em của trung tâm đã seed nhìn thấy gì, và làm bài thật

Mọi màn hình trước đều là của giáo viên và quản trị. Bản này đi cùng dữ liệu ấy nhưng từ phía `hs001` — một
trong 150 học sinh, 6 bài đã nộp, 4 chuyên đề yếu — **và làm nốt bài ôn cá nhân đang mở**.

Environment `e2e-hs01` trỏ vào tài khoản seed; `required: false` vì đây là một vòng xem, không phải bằng chứng
của Unit of Work nào.

Một viewport: đây là kiểm chứng **có gì để xem và làm được**, không phải kiểm tra responsive.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert | Env |
|---|---|---|---|---|---|---|
| S1 | Bài được giao: đã làm 6, còn một bài ôn đang mở | `/home` | `settle 4000; settle 1500` | data | `text=Ôn cá nhân`; `text=Đã làm`; `no-text=Có lỗi xảy ra` | e2e-hs01 |
| S2 | Tiến độ của tôi: mức nắm vững của chính em | `/me/stats` | `settle 4000; wait h1:has-text("Tiến độ của tôi"); settle 1500; scroll text=Mức nắm vững; settle 1500` | data | `text=Mức nắm vững`; `text=Cần ôn`; `no-text=Chưa có dữ liệu làm bài` | e2e-hs01 |
| S3 | Mở bài ôn cá nhân, khung làm bài hiện ra | `/home` | `settle 4000; click button:has-text("Bắt đầu"); settle 6000` | data | `count [data-testid=exam-question] = 1`; `no-text=Có lỗi xảy ra` | e2e-hs01 |
| S4 | Xem toàn đề thay vì từng câu | `/home` | `settle 4000; click button:has-text("Làm tiếp"); settle 6000; click [role=radio]:has-text("Toàn đề"); settle 3000` | data | `no-text=Câu sau`; `no-text=Có lỗi xảy ra` | e2e-hs01 |
| S5 | Trả lời vài câu rồi nộp | `/home` | `settle 4000; click button:has-text("Làm tiếp"); settle 6000; click [data-testid=option-A] >> nth=0; settle 2000; click button:has-text("Câu sau"); settle 1500; click [data-testid=option-B] >> nth=0; settle 2000; click button:has-text("Nộp bài"); settle 1500; click [role=dialog] button:has-text("Nộp bài"); settle 6000` | data | `count [data-testid=score10] = 1`; `no-text=Có lỗi xảy ra` | e2e-hs01 |
| S6 | Kết quả: điểm, từng câu, chuyên đề yếu của bài ấy | `/home` | `settle 4000; click a:has-text("Xem kết quả") >> nth=0; settle 5000; settle 1500` | data | `no-text=Có lỗi xảy ra`; `no-text=Không tải được` | e2e-hs01 |

## Không kiểm ở đây

- **Điểm bao nhiêu.** Bài này chỉ trả lời hai câu rồi nộp, nên điểm sẽ thấp và **đó là điều đúng để xảy ra**:
  thứ cần chứng minh là học sinh làm được và hệ thống chấm được, không phải em ấy giỏi.
- **Con số của trung tâm có đúng không.** Sáu bài trước của `hs001` do script làm hộ.

## Notes

**S5 ghi một lượt làm bài thật** và không hoàn tác được — bài đã nộp không xoá được qua sản phẩm, và điều đó
đúng: một câu trả lời thật không nên là thứ xoá được. Đề ôn cá nhân của `hs001` chuyển từ "Chưa làm" sang đã nộp,
`answer_facts` tăng, mức nắm vững của em ấy dịch theo. Đây là dữ liệu seed trong tổ chức dev, và bài ôn ấy sinh ra
để được làm.

Nút vào bài là **"Bắt đầu"** lần đầu và **"Làm tiếp"** khi đã có lượt đang dở — S3 mở lượt ấy ra, nên từ S4 trở đi
luôn là trường hợp thứ hai. Bài học này đã trả giá ở `.ai/e2e/teaching-loop`.

`"Nộp bài"` là nhãn của **cả** nút trên thanh **lẫn** nút xác nhận trong hộp thoại, nên cú nhấp thứ hai phải giới
hạn trong `[role=dialog]`; không thì nó chỉ mở lại hộp thoại vừa đóng.
