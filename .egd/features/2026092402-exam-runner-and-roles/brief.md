# Màn hình làm bài đứng yên, xem được cả đề, và giáo viên thử được đề mình giao

## Problem
Loc Tran, sau khi xem vòng chạy end-to-end (chat, 2026-09-24):

- **Màn hình làm bài nhảy layout.** Khung câu hỏi co giãn theo nội dung từng câu: một câu trả lời ngắn cho khung
  hẹp, một câu trắc nghiệm bốn phương án dài cho khung rộng, và học sinh thấy cả trang giật mỗi lần chuyển câu.
  Nguyên nhân nằm ở một dòng CSS: `Runner` là `mx-auto max-w-5xl` bên trong một flex column, mà `margin: auto`
  trên trục ngang **huỷ `stretch`** — khung tự co về đúng bề rộng nội dung.
- **Chỉ nhìn được một câu.** Không có cách nào xem cả đề để ước lượng rồi chọn làm câu dễ trước — điều mọi học
  sinh đều làm với một tờ đề giấy.
- **Giáo viên không thử được đề mình vừa giao.** `start_attempt` chặn thẳng `role != "student"`, nên người ra đề
  không có cách nào ngồi vào ghế học sinh để kiểm lại trước giờ làm bài.
- **Vai trò đang phẳng.** Học sinh, giáo viên và quản trị là ba tập rời nhau. Đúng ra phải lồng nhau:
  HS ⊂ GV ⊂ Admin — việc gì học sinh làm được thì giáo viên cũng làm được, cộng phần của giáo viên.

## Outcome
---
feature: exam-runner-and-roles
slug: 2026092402-exam-runner-and-roles
owner: Loc Tran
created: 2026-09-24
status: approved
---

## Success signal
Học sinh chuyển giữa mười câu của một đề THPT mà bề rộng khung không đổi một pixel; bật "Toàn đề" là đọc được cả
đề và trả lời ngay tại đó. Giáo viên mở đề vừa giao, làm thử, thấy điểm — và báo cáo lớp không đổi một con số.

## Out of scope
- Đổi cách chấm hay thang điểm
- Cho giáo viên được **giao bài** cho chính mình, hay có hồ sơ học tập của riêng mình
- Làm bài offline, tự lưu khi mất mạng

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Học sinh làm bài | Trang giật mỗi lần chuyển câu; chỉ thấy một câu | Khung đứng yên; xem được cả đề và làm câu nào tuỳ ý |
| Giáo viên ra đề | Không ngồi thử được đề đã giao | Chạy thử đúng màn hình của học sinh, có điểm, không ghi gì |
| Quản trị | Thấy ít hơn giáo viên ở phần học tập | Thấy mọi thứ giáo viên thấy, và giáo viên thấy mọi thứ học sinh thấy |

## Constraints
| Kind | Detail |
| --- | --- |
| Data | Không migration. Lần chạy thử của giáo viên **không sinh một dòng nào**: không attempt, không answer_facts, không mastery |
| UI | shadcn; giữ nguyên bảng câu, đồng hồ và cơ chế tự lưu của học sinh |
| Contract | Chạy thử là endpoint riêng, không mượn đường của attempt |
