---
name: ingestion-change
description: Change the document pipeline (MathType/LaTeX, splitter, header detection, images, AI fallback, duplicate handling) without moving the golden numbers.
---

# Change the ingestion pipeline

The pipeline reads teacher-supplied .docx/.pdf files: extract → header metadata → split into questions →
optional AI fallback → persist → triage (near-duplicates) → topic suggestion. Pure logic lives in
`modules/ingestion/domain/services/` (mtef, docx_ast, splitter, header, lines, ai_parse); anything that shells out
or calls a service lives in `infrastructure/adapters/` (LibreOffice, pdfium, OCR, LLM, storage).

## The safety net

The 18 official papers are the contract. Before and after any change:

```bash
EXAMIN_DIR=/path/to/papers ./scripts/verify.sh apps/api/tests/test_golden_official.py
```

Current numbers: 18 documents → **396/396 questions, 393 with answers, 386/386 solutions, 0 pictures lost**
(the live run through the worker also reports 7,887 formulas and 31 vector figures). A change that moves any of
them is wrong until the diff is explained and the expectations are updated on purpose.

## Working rules

- A parsing rule is a pure function with a fixture: add the smallest input that shows the case to
  `tests/test_splitter*.py`, `tests/test_mtef.py` or `tests/test_header_meta.py` before changing the code.
- Never "fix" one paper by special-casing its wording; find the pattern that generalises.
- Keep warnings: what the parser could not read must reach the teacher through the document log, not be dropped.
- A re-parse keeps approved questions and questions an exam uses; `question_count` counts both.
- Uploads deduplicate by content hash; `on_duplicate` is skip | replace | keep_both.

## After

`./scripts/verify.sh apps/api/tests` (full suite) plus the golden run, and say both results with their numbers.
