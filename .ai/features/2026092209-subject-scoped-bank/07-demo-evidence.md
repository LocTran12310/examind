# Demo evidence — subject-scoped-bank

## UOW-01 — Tags by subject, filters, facets (2026-09-22)
- Migration 0016 on dev DB; backfill tested by downgrade/upgrade (`test_tags_subject.py`): single-subject tags get
  the subject, mixed and nguồn đề tags stay shared.
- `/questions/facets`: each facet ignores its own filter; topic counts are subtree totals of the chosen subject
  (`test_bank_facets.py`). `subject_id=none`, `school_year`, tag groups (OR inside a group, AND across groups).

## UOW-02 — Bank UI (2026-09-22, live stack)
- /org/bank opened on the subject with most questions (Toán 85) and shows "Chưa phân môn 437" (the reference files
  uploaded by earlier golden runs before header detection; "Tách lại" fills their subject).
- "Bộ lọc · Toán" sheet lists only Toán topics with subtree counts (Đại số 5, Giải tích 4, Hình học 7 …), đợt, năm học,
  nguồn đề, tags, trạng thái; "Áp dụng" writes the URL; chips remove single filters.
- Exam matrix loads `/topics?subject_id=` and `/tags?subject_id=` of the exam's subject; Tags page has a Môn column
  and a subject in the form (nguồn đề forced shared).
- Tests: `bank.test.tsx` (sheet, chips, default subject, switch drops topic/tag), `tags.test.tsx`; 128 web tests,
  `tsc`, `eslint`, `next build` clean.
