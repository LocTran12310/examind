---
feature: official-exam-ingestion
slug: 2026092208-official-exam-ingestion
owner: Loc Tran
created: 2026-09-22
status: approved
---

# Intent — Read official exam files (THPT 2025 thi thử) correctly

## Problem
The official exam files Loc Tran uses as the reference (18 "Thi thử TN THPT 2025 môn Toán" .docx)
write every formula as a MathType OLE object (7 889 in total, no OMML). The pipeline keeps only the
WMF preview picture, which browsers cannot show, so imported questions are unreadable. WMF/EMF
figures (hình chóp, đồ thị, bảng biến thiên) are dropped. Answers written in the solution section
("Câu | 1 | 2 / Đáp án | 3 | 20", "a đúng| b sai") are missed for 83 of 390 questions, one file loses
its Phần III and another its solutions. Uploaders retype subject, grade, year and exam kind that the
header already states, and upload one file at a time.

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Uploader | Uploads one file, fills subject/grade/year/đợt by hand | Drops a whole folder; header metadata is pre-filled, confirm only |
| Reviewer | Sees broken pictures instead of formulas, fills answers by hand | Sees KaTeX formulas and PNG figures, answers and solutions already attached |
| Teacher | Rebuilds the original exam question by question | "Tạo đề từ tài liệu": draft exam in original order with THPT 2025 points |

## Success signal
On the 18 reference files: 396/396 questions found, ≥ 98 % with an answer, every question with a
solution when the file has one, and no WMF/EMF picture left in any question.

## Out of scope
- Subject-scoped filters (next feature, F10)
- PDF/scan changes
- Equation editor for MathType round-trip (export back to Word)

## Constraints
| Kind | Detail |
| --- | --- |
| Cost | Free, self-hosted: own MTEF parser, LibreOffice headless |
| Safety | A formula or picture that cannot be converted is kept as before with a warning — never lost |
| Compatibility | Existing splitter behaviour and golden set stay green |
