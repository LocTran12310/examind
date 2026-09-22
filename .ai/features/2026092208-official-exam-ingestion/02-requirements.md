---
feature: official-exam-ingestion
stories: 5
acceptance_criteria: 12
---

# Requirements — Read official exam files correctly

## US-01 — Formulas become LaTeX
As a reviewer I want MathType formulas shown as real math, not broken pictures.

**Priority:** must

**AC-01** — MathType OLE → LaTeX
```gherkin
Given a .docx whose formulas are MathType OLE objects (Equation.DSMT4, MTEF v5)
When it is imported
Then each formula appears in the question as $…$ LaTeX that KaTeX renders, including fractions, roots, systems, vectors, integrals with limits, lim, sub/superscripts and degrees
```

**AC-02** — Unreadable formula is not lost
```gherkin
Given a formula object whose data cannot be converted
When it is imported
Then its preview picture is kept (converted to PNG) and the document shows a warning with the count
```

## US-02 — Vector pictures become PNG
**Priority:** must

**AC-03** — WMF/EMF figures
```gherkin
Given a figure stored as WMF or EMF
When it is imported
Then the question shows a trimmed PNG of it
And when the converter is unavailable the old warning is shown and the job still succeeds
```

## US-03 — THPT 2025 layout with a solution section
**Priority:** must

**AC-04** — Per-part answer tables
```gherkin
Given a solution section with rows "Câu | 1 | 2 …" and "Đáp án | 3 | 20 …" under each PHẦN header
When the file is split
Then those values become the answers of that part's questions (letters for Phần I, Đ/S for Phần II, values for Phần III)
```

**AC-05** — Lower-case true/false verdicts
```gherkin
Given "Đáp án: a đúng| b sai| c sai| d đúng" in a solution
When split
Then the four statements get true/false/false/true
```

**AC-06** — Solution section without a header
```gherkin
Given the questions restart at PHẦN I Câu 1 after the exam without a "HƯỚNG DẪN GIẢI" title
When split
Then the second pass is read as solutions and merged into the first, not duplicated
```

**AC-07** — Look-alike letters and methods
```gherkin
Given an option label typed with a Cyrillic "А" and a solution with "Phương pháp:" and "Cách giải:"
When split
Then the option is read as A and both parts stay in the solution as bold sub-headings
```

**AC-08** — Reference set
```gherkin
Given the 18 reference files
When the golden run imports them
Then 396/396 questions are found, at least 98 % have an answer, every question with a solution in the file has it, and no WMF/EMF picture remains
```

## US-04 — Header metadata and multi-file upload
**Priority:** should

**AC-09** — Header suggestions
```gherkin
Given a file whose header reads "SỞ GD&ĐT … / ĐỀ THI THỬ TỐT NGHIỆP LẦN 1 / NĂM HỌC: 2024 - 2025 / MÔN: TOÁN / Thời gian làm bài: 90 phút"
When it is parsed
Then the document stores issuer, school year, subject, exam kind "thi thử", attempt 1, grade 12 and duration 90, and its questions inherit subject, grade and đợt when the uploader left them empty
```

**AC-10** — Several files at once
```gherkin
Given I drop 18 files in the upload form
When I confirm
Then 18 documents are queued with the same settings, and a file already uploaded is reported as duplicate without stopping the others
```

## US-05 — Exam from a document
**Priority:** should

**AC-11** — Draft exam in original order
```gherkin
Given a parsed document with Phần I/II/III questions
When I choose "Tạo đề từ tài liệu"
Then a draft exam is created with the questions in part/number order and points 0,25 / 1 / 0,5 per part
```

**AC-12** — Only usable questions
```gherkin
Given some questions of the document are rejected or duplicates
When the exam is created
Then those are skipped and the result says how many were skipped
```
