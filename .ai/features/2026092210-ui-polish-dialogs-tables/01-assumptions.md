---
feature: ui-polish-dialogs-tables
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | Every FormDialog gets ⤢ maximise (also double-click on the title) and edge/corner resizing; sizes reset when the dialog closes | high | no | Dialog UX | confirmed | Confirmed by Loc Tran in chat (2026-09-22): "Modal/Dialog thêm chức năng phóng to, Kéo ở cạnh cho to/nhỏ được giống back-office" |
| A-02 | Back links and "Hủy/Lưu" returns go to the last URL of that list in this tab (sessionStorage), falling back to the plain list | high | no | Navigation | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-03 | The save shortcut listens to the physical Enter key (`code`) with ⌘ or Ctrl, so Vietnamese IME composition does not swallow it; the hint shows ⌘ on Apple devices | medium | no | Shortcut | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-04 | Question editor topics are limited to the question's subject when it has one (as in the bank, F10) | medium | no | Editor | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
