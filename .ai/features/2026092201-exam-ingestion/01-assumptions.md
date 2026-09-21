---
feature: exam-ingestion
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | Vietnamese exams mark questions with `Câu N` (optionally `Câu N.`, `Câu N:`, `Câu N (0,25 điểm)`), options with `A.`–`D.` (also `A)`), true/false statements with `a)`–`d)` | high | yes | Splitter rules | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-02 | Answers appear as one of: inline `Đáp án: C` / `Chọn C`; an answer-key table/list at the end (`1.A 2.C`, or a table); or the correct option underlined/bold/coloured in Word | medium | yes | Answer attachment | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-03 | Solutions appear either right after each question (`Lời giải`, `Hướng dẫn giải`, `Giải`) or in a trailing section whose items restart numbering at `Câu 1` | medium | yes | Solution attachment | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-04 | THPT 2025 structure: `PHẦN I` MCQ, `PHẦN II` true/false (4 statements), `PHẦN III` short answer; older exams are all-MCQ; essays exist in school exams (`Bài N`) | medium | no | Type detection | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-05 | Docx equations are OMML (Word 2007+); Pandoc converts them to TeX. MathType objects stay images | medium | no | Math fidelity | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-06 | Scans are printed text; Tesseract `vie` gives usable text; formulas in scans are imperfect and flagged low-confidence | medium | no | Scan quality | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-07 | Max upload 30 MB, 60 pages; .docx, .pdf, .png, .jpg accepted; .doc (binary) rejected with a hint to save as .docx | high | no | Upload validation | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-08 | Same file (sha256) uploaded twice in one org returns the existing document instead of parsing again | high | no | Duplicate handling | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-09 | Worker processes at most `INGEST_CONCURRENCY` (default 1) jobs; a job retries up to 2 times with backoff; a stuck job (locked > 15 min) is re-queued | medium | no | Throughput | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-10 | LLM providers: `ollama` (native API), `openai` (any OpenAI-compatible server incl. LM Studio, vLLM, Gemini's OpenAI endpoint), `anthropic`; API keys encrypted at rest with a key from env `APP_ENCRYPTION_KEY` | medium | yes | Model registry contract | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-11 | System-wide models (organization_id NULL) are managed by super_admin and visible to every org; org models by org_admin | medium | no | Registry permissions | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-12 | Parsed questions are stored as `status = draft` with `confidence` 0–1 and `issues[]`; approval happens in `question-review` | high | yes | Handoff to feature 3 | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-13 | Topic suggestion in this feature: keyword match against leaf topic names (always) + LLM choice among leaf topics when a text model is configured; stored as `question_topics.source = 'auto'` with a score | medium | no | Suggestion quality | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-14 | Re-parsing a document replaces its draft questions; questions already approved are never deleted by a re-parse | high | yes | Data loss | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
