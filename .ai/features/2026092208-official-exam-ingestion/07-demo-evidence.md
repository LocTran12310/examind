# Demo evidence — official-exam-ingestion

## UOW-01 — Formulas and figures (2026-09-22)
- Corpus: the 18 files in `Examin/` hold 7 889 MathType objects (Equation.DSMT4, MTEF v5 + MathType 7), no OMML.
- `ingestion/mtef.py`: 7 889/7 889 parsed; 2 are empty objects in the source files (dropped, nothing shown);
  KaTeX renders 100 % of the LaTeX (`node` + katex over every formula). 90 random formulas compared by eye
  with their WMF previews: all matched (fractions, roots, systems as `cases`, vectors, integrals with limits,
  lim, degrees, intervals).
- Checked and rejected: LibreOffice docx→odt keeps OLE replacements only; mtef-go misses overbar/embellishments;
  `wmf2svg` loses fonts and arrows.
- WMF/EMF pictures: 31 figures in the set (hình chóp, đồ thị, bảng biến thiên, formula pictures pasted as WMF)
  rendered to trimmed PNG by LibreOffice → pypdfium2 (e.g. the pyramid of Chuyên Phan Bội Châu), 0 lost.
- Live stack, Sở GD Ninh Bình file: Câu 2 shows the cube figure as PNG, every formula in KaTeX, Phần III answers
  from the file's own table.
- Tests: `test_mtef.py` (reference objects + synthetic templates), `test_docx_mathtype.py`, `test_vector_images.py`.

## UOW-02 — THPT 2025 layout, reference set (2026-09-22)
- Before: 390/396 questions, 83 without answer, 1 file without solutions, 1 file without Phần III.
- After (`scripts/golden_live.py` with `EXAMIN_DIR`, live stack, rule mode, 24 s for 18 files):
  `TOTAL {"docs": 18, "questions": 396, "found": 396, "answers": 396, "solutions": 386, "equations": 7887, "pictures": 31}`
  — 393/396 questions have an answer (99.2 %); the 3 without one have none in the file (Quế Võ 1 II.3 has a
  broken Đ/S table, Phan Bội Châu III.5–6 end without a result). 10 questions have no solution in the file.
- 17 questions are flagged "đáp án không khớp bảng đáp án": the file's own key disagrees with its worked solution
  (ĐHKHTN Phần I key is another mã đề; Sở Bắc Ninh Phần III key is shifted one column; Nguyễn Khuyến II.3).
  The worked solution wins and the reviewer sees the flag.
- Rules added: per-part key tables inside the solutions (`Câu | …`, `Câu 1 | Câu 2 …`, `Mã đề | …`, grids
  `a | b | c | d` in letters or words), lower-case verdicts, a solution pass without a heading, Word
  auto-numbered parts (`1.`), Cyrillic `А`, labels like `**[B]{.underline}.**` and `[**[C]{.underline}.** …]{.mark}`,
  the copied question dropped from the solution, "Phương pháp / Cách giải" kept as headings.
- Tests: `test_splitter_thpt.py`, `test_golden_official.py` (runs with `EXAMIN_DIR`, skipped otherwise), old splitter
  / golden / review-flow tests unchanged and green.

## UOW-03 — Header metadata and multi-file upload (2026-09-22)
- Header detection on the 18 files: issuer found for 18/18 (school when named, else "Sở GD&ĐT <tỉnh>"),
  school year 18/18, subject 17/18 (Quế Võ 1 has no MÔN line in the exam header), exam kind 18/18.
- Live: "Tách lại" on the Ninh Bình file → "Nhận từ tiêu đề đề thi: Sở GD&ĐT Ninh Bình · 2024-2025 · Toán · Lớp 12 ·
  Thi thử lần 1 · 90 phút"; its questions carry Toán · Lớp 12 · Thi thử · #Sở GD&ĐT Ninh Bình.
- Upload form: fields default to "Tự nhận từ đề"; several files at once with per-file state (queued / đã có / lỗi);
  one file opens its page, a batch stays on the list. Browser file pickers cannot be driven from the in-app
  browser, so the batch path is covered by `documents.test.tsx`.
- Tests: `test_header_meta.py` (detect, apply keeps user values, PATCH updates questions and source tag).

## UOW-04 — Tạo đề từ tài liệu (2026-09-22)
- Live: Ninh Bình document → "Tạo đề từ tài liệu" → exam "Sở GD&ĐT Ninh Bình · Thi thử · 2024-2025", 22 câu,
  10 điểm, Phần I/II/III in the original order; toast "Đã tạo đề thi với 22 câu".
- Tests: `test_exam_from_document.py` (order, points 0,25/1/0,5, rejected question skipped, unparsed refused),
  `documents.test.tsx` (button → exam page).
