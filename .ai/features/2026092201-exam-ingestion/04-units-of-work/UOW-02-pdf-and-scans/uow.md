---
id: UOW-02
slug: pdf-and-scans
title: Text PDFs and scanned exams are read
demoable: true
duration: 2d
depends_on: [UOW-01]
requirements: [US-03]
verifies: [AC-11, AC-12]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Text PDFs and scanned exams are read

## Demo script
1. Upload samples/exams/de-mau-toan10.pdf → 40 questions, figure cropped into the right question
2. Upload samples/exams/de-scan.png (and de-scan.pdf) → questions split, each flagged 'OCR' with confidence ≤ 0.8

## In scope
- pdfplumber extractor with two-column ordering and image crops
- OCR provider interface + Tesseract
- PDF/scan samples + golden tests

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| Two-column PDFs mis-ordered | Column detection by word x-gap; tested on a two-column sample |

## Definition of done
- [ ] All of AC-11, AC-12 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
