---
feature: official-exam-ingestion
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | The 18 files in `Examin/` are representative of the official files centers upload (MathType OLE, three-part THPT 2025 layout, solution section repeating questions) | high | yes | Parser design | confirmed | Confirmed by Loc Tran in chat (2026-09-22): "Đây là tài liệu chính thức, có thể làm mẫu được" |
| A-02 | MathType is converted by our own MTEF v5 reader (no maintained Python package exists); template/embellishment numbering follows the MathType SDK as used by zhexiao/mtef-go (Apache-2.0, credited) | high | yes | Formula fidelity | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-03 | WMF/EMF pictures are rendered with LibreOffice headless (→ PDF → pypdfium2 PNG, trimmed); the API/worker image grows by ~300 MB; without soffice the old warning path applies | medium | no | Image size / figures | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-04 | "Phương pháp" and "Cách giải" stay inside the solution markdown as bold sub-headings, not separate columns | medium | no | Solution display | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-05 | Header metadata (issuer, school year, subject, exam kind, attempt, duration) is a suggestion shown in the upload/document form; the user's values win | high | no | Tagging | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-06 | "Tạo đề từ tài liệu" makes a draft exam with the document's parsed questions in original part/number order, points 0,25 (Phần I), 1 with THPT partial ladder (Phần II), 0,5 (Phần III) | medium | no | Exam creation | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-07 | Multi-file upload creates one document per file with the same processing settings; duplicates (same hash) are reported per file and skipped | high | no | Upload | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-08 | Expected answers for the golden set are taken from each file's own answer tables and spot-checked by hand; the files stay outside the repo (only derived expectations are committed) | medium | no | Evaluation | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
