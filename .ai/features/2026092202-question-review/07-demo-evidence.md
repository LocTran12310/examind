# Demo evidence — question-review

Run 2026-09-22 on the compose stack (http://localhost:8088), org TrungtamA.

| UoW | Step | Result | How |
| --- | --- | --- | --- |
| UOW-01 | /org/review lists every parsed exam with Tự duyệt / Cần xem / Kiểm tra ngẫu nhiên / Trùng counts, progress bar, reviewer select | as specified | Browser screenshot |
| UOW-01 | Golden docx: flagged share | de-mau-toan10 0/40, de-thpt2025 0/22 flagged; 2 spot checks | pytest `test_triage.py`, `test_review_flow.py` |
| UOW-01 | PDF copy of the Word exam → duplicates linked to originals | ≥ 36/40 duplicate; template variants with other numbers not flagged | pytest; live: scan Câu 6 marked duplicate of the docx one |
| UOW-01 | Assignment + "Của tôi" | as specified | pytest `test_review_api.py` |
| UOW-02 | Keyboard queue on de-scan.pdf: source page image beside the question; `4` sets D, `Enter` approves → 2/9 | as specified | Browser (real key events) |
| UOW-02 | Blocking issue on Enter → message, stays | as specified | vitest `ReviewQueue.test.tsx` |
| UOW-02 | Inline editor with KaTeX preview, Ctrl+Enter, image paste → asset ref | as specified | vitest `QuestionEditor.test.tsx` |
| UOW-02 | Answer-key paste, approve-confident, PDF page PNG cached | as specified | pytest `test_review_bulk.py` |
| UOW-02 | Review flow on golden docs | ≤ 15% flagged, ≤ 2 actions per reviewed question | pytest `test_review_flow.py` |
| UOW-03 | kNN: approved question's topic suggested for a near-identical new one (source knn) | as specified | pytest `test_knn.py` |
| UOW-04 | /org/bank?q=parabol → 15 matches with type/status/topic chips | as specified | Browser screenshot |
| UOW-04 | Topic subtree filter, tags, create/delete/restore, bulk, 10k search < 300 ms | as specified | pytest `test_bank_api.py`; vitest `bank*.test.tsx`, `question-edit.test.tsx` |

Findings fixed during the demo: OCR glues option labels to their text ("D.14", "C.Ø") → splitter accepts a
label followed directly by a non-space; OCR-flagged questions could not be approved by hand → split
"blocks auto-approval" from "blocks manual approval" (ADR-05).
Legacy note: questions parsed before this feature were triaged once on API boot without dedupe (both the
docx and the PDF copy of the sample remain usable in the dev DB).
Test totals at close: API 146 passed, web 59 passed.
