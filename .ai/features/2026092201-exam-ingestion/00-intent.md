---
feature: exam-ingestion
slug: 2026092201-exam-ingestion
owner: Loc Tran
created: 2026-09-22
status: approved
---

# Intent — Exam ingestion

## Problem
Teachers own years of exams as Word and PDF files (some scanned). Re-typing them into a
question bank is the reason banks never get built. Examind must read those files itself and
split them into complete questions — stem, options, answer, solution and every figure —
already filed under subject, grade, semester and a suggested topic, so a teacher only
confirms instead of typing.

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Teacher | Copies questions by hand into Word/Excel | Drops a .docx/.pdf, sees 40 parsed questions in about a minute |
| Center admin | — | Chooses which OCR engine and which AI model (local, free by default) the center uses |

## Success signal
On the bundled sample set (docx with OMML math + images, text PDF, scanned image PDF), the
rule-based pipeline alone splits ≥ 95% of questions correctly with answers attached for
docx/text PDF, and a 40-question docx is parsed in < 60 s on the dev machine without any
LLM. (Measured by `apps/api/tests/test_ingestion_golden.py`.)

## Out of scope
- Teacher review queue, approve/reject, bulk actions, dedupe (feature `question-review`)
- Embedding-based topic suggestion (kNN) — needs approved questions; `question-review`
- MathType OLE objects converted to LaTeX (kept as images)
- Handwritten scans
- Paid providers enabled by default (supported, off unless an admin adds a key)

## Constraints
| Kind | Detail |
| --- | --- |
| Cost | Free/open-source engines only by default (Pandoc, pdfplumber, pypdfium2, Tesseract, Ollama) |
| Licence | Avoid AGPL libraries in the SaaS-shaped service (no PyMuPDF) |
| Hardware | Oracle Ampere 4 OCPU / 24 GB: ≤ 2 concurrent ingestion jobs; LLM optional |
| Models | Never hard-coded: chosen per org and per upload from a registry |

## Existing surface touched
- Reused: `Question`, `Asset`/`store_image`, `QuestionView`, topic tree, `OrgScope`, `staff_scope`
- New: `jobs` queue + worker container, `source_documents`, `ai_models`, `question_topics`, `question_tags`
- Entry points: `/org/documents`, `/org/documents/[id]`, `/org/ai-models`
