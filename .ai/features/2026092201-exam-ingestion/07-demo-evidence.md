# Demo evidence — exam-ingestion

Run 2026-09-22 on `docker compose --profile ai up` (Mac M-series, Docker 16 GB, CPU only).

| UoW | Step | Result | How |
| --- | --- | --- | --- |
| UOW-01 | Upload de-mau-toan10.docx → parsed | 40/40 questions exact (type, options, answer), images in Câu 5 option C, Câu 8 stem, Câu 12 solution | curl through Caddy + browser screenshot; golden test |
| UOW-01 | de-thpt2025-toan.docx | 22/22 (12 MCQ, 4 true/false with Đ/S, 6 short answers) | golden test |
| UOW-01 | Duplicate upload, .doc/.exe refused, broken docx → "Lỗi" | as specified | pytest `test_documents_api.py` |
| UOW-01 | Parse time | ~0.3 s for 40 questions (< 60 s target) | document log |
| UOW-02 | de-mau-toan10.pdf | 40 questions, 7 pages, figures cropped | worker on stack |
| UOW-02 | de-2cot.pdf (two columns) | 10/10 | worker on stack + pytest |
| UOW-02 | de-scan.pdf / de-scan.png (Tesseract vie) | 10 / 5 questions, all flagged OCR ≤ 0.8 | worker on stack |
| UOW-03 | Discover real Ollama, add qwen2.5:1.5b, "Kiểm tra" | ok, 21.9 s | curl through Caddy |
| UOW-03 | Rule + AI on de-kho.docx with the real model | every call timed out (120 s); questions kept rule results with "AI không phản hồi" (AC-19 verified live) | worker logs |
| UOW-03 | Direct measurement | qwen2.5:1.5b CPU-in-Docker with JSON schema: 104 tokens in 254 s; wrong labels/type (normalised now) | direct call |
| UOW-03 | AI replacement, chain fallback, vision OCR, re-parse, org defaults | as specified | pytest with stub model server |
| UOW-04 | Suggested topic chips on the PDF document | e.g. "Tìm đỉnh và trục đối xứng parabol · 78% · gợi ý" | browser screenshot |
| UOW-04 | Golden topic accuracy | ≥ 90% (node or descendant) | pytest `test_topic_suggest.py` |

**Finding for final review:** the AI path is wired end to end, but a useful local model needs
either native Ollama with Metal on the Mac (not Docker), a GPU/≥ 7B model on the VM, or a free
API tier registered as an OpenAI-compatible model; raise `LLM_TIMEOUT_SECONDS` for slow CPUs.
Test totals at close: API 116 passed, web 40 passed.
