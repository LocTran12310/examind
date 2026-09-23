---
feature: topic-coverage
---

# Demo evidence

## UOW-01 — Untagged questions are listable, suggestible and no longer silent

Run on the live stack (`docker compose up -d --build api worker`, org `trungtama`, user `admin`), 2026-09-23.
Every call below is read-only; nothing in the live bank was changed.

### Checks

| Check | Result |
| --- | --- |
| `make lint-api` (ruff + lint-imports) | 4 contracts kept, 0 broken |
| `./scripts/verify.sh apps/api/tests` | **457 passed, 1 skipped** (3:02) |
| `EXAMIN_DIR=… ./scripts/verify.sh apps/api/tests/test_golden_official.py` | 18 documents → **396/396 questions, 393 answers, 386 solutions, 0 pictures lost** — unchanged |
| `scripts/close_ticket.sh … T-01-01 T-01-02 T-01-03` | exit 0, each with its own verified test run |

### 1. The queue (AC-01, AC-05)

`POST /questions/search {"has_topic": false}` → **102** questions (`"status": "all"` → 109, of which 7 are
already in review or rejected). `has_topic: true` and the unfiltered list are unchanged, and the filter composes
with `document_id`, `subject_id`, the column filters and the sort like every other bank filter.

`POST /questions/facets {}` → `topics["none"] = 102` and the new `untagged_documents`, 19 entries totalling 102:

| Untagged | Document |
| --- | --- |
| 10 | 09. THPT THUẬN THÀNH 1-2 - BẮC NINH |
| 7 | 14. SỞ GIÁO DỤC YÊN BÁI |
| 7 | 18. Huyện Cẩm Xuyên - Hà Tĩnh (Lần 1) |
| 7 | 2. THPT Lương Tài 2 – Bắc Ninh |
| 7 | 1. THPT Quế Võ 1 – Bắc Ninh |
| 7 | 12. CHUYÊN VĨNH PHÚC (Lần 1) |
| 6 | 19. Sở GD & ĐT Bà Rịa - Vũng Tàu |
| 6 | 10. THPT TRIỆU QUANG PHỤC - HƯNG YÊN |
| 6 | 07. THCS-THPT NGUYỄN KHUYẾN - TPHCM |
| 6 | 13. CHUYÊN PHAN BỘI CHÂU - NGHỆ AN |
| 6 | 20. Sở GD & ĐT Hà Tĩnh |
| 5 | 17. CHUYÊN VINH - NA (Lần 1) |
| 5 | 08. THPT VĂN GIANG - HƯNG YÊN |
| 5 | 6. THPT Thạch Thành 1 - Thanh Hóa (Lần 1) |
| 4 | 11. SỞ GIÁO DỤC NINH BÌNH |
| 4 | 3. Lê Thánh Tông – TP HCM |
| 2 | 15. CHUYÊN ĐHKHTN - HCM (Lần 1) |
| 1 | 16. SỞ BẮC NINH - KSCL |
| 1 | `none` (no source document) |

5–10 per paper, exactly as the intent described.

### 2. Suggestions (AC-02)

`POST /questions/suggest-topics` over all 102 (three batches of ≤50): **14 questions get at least one candidate**
(15 candidates: 13 `similar`, 2 `keyword`). Five of them, with the real topic names:

| Question | Candidate | Score | Source |
| --- | --- | --- | --- |
| Câu 5 — *Nghiệm của phương trình $3^{x-2}=9$ là* | Logarit | 0.54 | similar |
| Câu 2 — *… ước tính số người nhiễm bệnh kể từ khi xuất hiện bệnh nhân đầu tiên …* | Đạo hàm | 0.43 | similar |
| Câu 3 — *Số nghiệm của phương trình $\cot x=1$ trên đoạn $[-\pi; 2\pi]$ là* | Logarit | 0.37 | similar |
| Câu 5 — *Tập nghiệm của bất phương trình $(1/\pi)^{x}>1$ là* | Logarit | 0.55 | similar |
| Câu 9 — *Tập nghiệm của bất phương trình $3^{3x+1}<1/9$ là* | Logarit | 0.55 | similar |

The one question with keyword cues shows the three-candidate shape and the ordering:

*Cho hàm số $y = x^2 - 4x + 3$ có đồ thị $(P)$ …* → **Hàm số bậc hai và đồ thị** 0.73 `keyword`,
**Phương trình đường thẳng** 0.62 `keyword`.

Guard rails on the live stack: 51 ids → 422, a question of another organisation / an unknown id → 404.

**Quality, honestly.** Recall is 14/102. The backlog is by definition what the pipeline's own keyword cues could
not place, so the keyword pass adds almost nothing to it — the value comes from kNN, and only 13 of the 102 have a
neighbour above `KNN_MIN_SIMILARITY = 0.35`. Precision is mixed: the exponential equations and inequalities land on
**Logarit**, which is the right branch, while *$\cot x = 1$* → Logarit at 0.37 is a miss a teacher will reject in
one keystroke. The remaining 88 need the TopicPicker of UOW-02. This is the measurement A-05 asked for — if the
acceptance rate of the top suggestion stays this low, the assumption to revisit is A-05 (no tagging model in the
queue), not the queue itself.

### 3. The backlog stops refilling (AC-04)

`tests/test_topic_coverage.py::test_a_question_without_a_topic_waits_for_review`: re-uploading a paper the
classifier cannot place (`de-kho.docx`) leaves every one of its 8 questions `needs_review`, never `auto_approved`,
with the document log carrying `suggest_topics {none: 8}` and the warning
*"8 câu chưa gắn chuyên đề, đã chuyển sang chờ duyệt"*. The questions the classifier did place keep the status
triage gave them (`test_a_tagged_question_keeps_its_triage_outcome` on `de-mau-toan10.docx`).

Four existing tests encoded the old behaviour for `de-kho.docx` (3 of its 8 questions were auto-approved, one of
them a spot check) and were updated on purpose — see the report of the change. The golden numbers did not move and
the golden expectations were not touched.
