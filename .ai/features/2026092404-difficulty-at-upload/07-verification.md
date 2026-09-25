---
feature: 2026092404-difficulty-at-upload
environments: [local]
viewports: [desktop, mobile]
---

# Verification — mức độ hiện ngay chỗ đang duyệt, và sửa được tại đó

Chỉ UOW-04. Ba UoW kia không đổi một màn hình nào — một cột, một quy tắc thuần, một lượt model trong worker, một
script đo và một lệnh điền — và chúng được kiểm ở nơi kiểm được, như `uow.md` của chúng ghi.

Cần hàng đợi duyệt có câu: sau lần tách lại 18 đề, 20 câu đang ở `needs_review`.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert | Env |
|---|---|---|---|---|---|---|
| S1 | Thẻ duyệt nói mức độ là của máy hay của người | `/org/review` | `settle 3500; fill [aria-label="Lọc Đề"] = ĐHKHTN; settle 2500; click a[href^="/org/review/"]:not([href$="/untagged"]); settle 4500; scroll [data-testid=difficulty-button]; settle 1200` | AC-06 | `count [data-testid=difficulty-button] = 1`; `text=model gợi ý`; `no-text=Có lỗi xảy ra` | local |
| S2 | Giáo viên đặt lại mức ngay tại thẻ | `/org/review` | `settle 3500; fill [aria-label="Lọc Đề"] = ĐHKHTN; settle 2500; click a[href^="/org/review/"]:not([href$="/untagged"]); settle 4500; press j; settle 1500; click [data-testid=difficulty-button]; settle 1200; click [data-testid=difficulty-vdc]; settle 2500; scroll [data-testid=difficulty-button]; settle 1200` | AC-06 | `text=Vận dụng cao`; `no-text=Có lỗi xảy ra`; `no-text=Không tải được` | local |

## Không kiểm ở đây

- **Mức độ ấy có đúng không.** Không màn hình nào trả lời được câu đó; chỉ tỉ lệ làm đúng thật mới trả lời được,
  và trên tổ chức này nó đã bị dữ liệu seed làm hỏng (`.ai/e2e/centre/PLAN.md`).
- **S2 không khẳng định nguồn biến mất.** Nút hiện "Vận dụng cao" sau khi đặt, và phần nguồn rỗng đi vì
  `DIFFICULTY_SOURCE_LABEL["manual"]` là chuỗi rỗng — một `no-text=` trên "model gợi ý" sẽ **đỏ sai** khi thẻ kế
  tiếp trong hàng đợi vẫn mang nhãn của máy. Việc nguồn biến mất được chứng minh ở nơi so được hai trạng thái
  cạnh nhau: `ReviewQueue.test.tsx`, đúng một test khẳng định `not.toHaveTextContent("gợi ý")` sau khi đặt.

## Notes

S2 **ghi một thay đổi thật** vào ngân hàng: một câu trong hàng đợi đổi mức độ và dấu vết thành `manual`. Cố ý và
không hoàn tác — chính `manual` là thứ AC-04 nói không lượt máy nào được đụng tới, nên để lại một câu như vậy là
để lại đúng thứ cần có.

**Và đó là lý do S1 đọc câu đầu còn S2 sang câu thứ hai** (`press j`). Bản đầu để cả hai dùng cùng một câu, và
runner lặp viewport ở vòng ngoài: S2 trên desktop đặt câu ấy thành `manual`, nên S1 trên mobile không còn thấy
"model gợi ý" và đỏ — một bước **ghi** đã làm tiền đề của một bước sau thành sai. Bước đỏ ấy trông y hệt một lỗi
thật, và nó không phải.

Cả hai mở đề **theo tên** chứ không theo thứ tự trong hàng đợi. Bản trước lấy `nth=0`, và đề đứng đầu hôm ấy chỉ
còn **một** câu — một mẫu kiểm chứng — nên `press j` không đi đâu được và hai bước lại rơi vào đúng một câu. Đề
"CHUYÊN ĐHKHTN" còn 11 câu chờ duyệt, đủ chỗ cho hai bước không giẫm lên nhau. Tên đề là tên file đã tải lên, ổn
định theo dữ liệu, không phải một id bị gắn cứng — nhưng **tên đề không phải link**. Lọc theo tên
trước rồi bấm link duy nhất còn lại — cùng cách S7 của `.ai/e2e/centre` dùng.

Và link ấy **không phải "Chi tiết"**: chữ đó là nút mở popover đếm số câu theo trạng thái
(`ReviewCounts.tsx:47`), bấm vào không đi đâu cả. Link mở đề là "Duyệt N câu", nên bước bám vào `href` của nó.
Mất ba lượt chạy đỏ mới nhìn ra, và cả ba lần tôi đều đoán selector thay vì đọc component.
