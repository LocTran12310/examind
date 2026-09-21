---
id: UOW-01
slug: word-exam-to-questions
title: A Word exam becomes complete draft questions
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02]
verifies: [AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08, AC-09, AC-10, AC-21]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — A Word exam becomes complete draft questions

## Demo script
1. docker compose up -d --build (worker included)
2. Log in as a trungtama teacher, open /org/documents
3. Upload samples/exams/de-mau-toan10.docx with Toán · Lớp 10 · HK1 · Giữa kỳ
4. Status goes Đang chờ → Đang xử lý → Đã tách (40 câu) within a minute
5. Open the document: every question shows stem, 4 options, answer, solution; equations render; the figure in Câu 5's option C and in Câu 12's solution appear
6. Upload the same file again → redirected to the existing document with 'File này đã được tải lên'
7. Upload a .doc → field error
8. Upload samples/exams/de-thpt2025-toan.docx → PHẦN I mcq, PHẦN II true/false with Đ/S, PHẦN III short answers

## In scope
- Worker + Postgres job queue
- Documents schema and API
- Pandoc docx extractor
- Rule-based splitter (answers, answer keys, trailing solutions, parts, confidence)
- Documents UI (upload, list, detail with QuestionView)
- Sample exam files + golden test

## Not in scope
- PDF/scans (UOW-02)
- AI models and fallback (UOW-03)
- Topic suggestion (UOW-04)

## Risks
| Risk | Mitigation |
| --- | --- |
| Real exams deviate from the sample formats | Splitter rules isolated and table-tested; golden set extended with real files at final review |

## Definition of done
- [x] All of AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08, AC-09, AC-10, AC-21 pass
- [x] Worker image builds on arm64 with pandoc and tesseract
- [x] 40-question docx parsed < 60 s
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
