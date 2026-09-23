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

## UOW-02 — The tagging queue clears the backlog

Run on the live stack (`docker compose up -d --build web`, org `trungtama`, user `admin`, http://localhost:8088),
2026-09-23, on the real bank — the topics assigned below are a real change and were meant.

`Duyệt câu hỏi › Chưa gắn chuyên đề` (`/org/review/untagged`, new nav item under "Đề & câu hỏi"). The body of the
list is `{has_topic: false, page, limit, sort: [{created_at, desc}], status: "all", subject_id?, document_id?}` —
`status: "all"` because a question the classifier could not place is `needs_review` since UOW-01 and would fall out
of the default `usable` filter.

### AC-01 — the queue
109 câu on opening, newest first, each row with its stem through the bank's renderer (KaTeX and the parsed images),
the subject, the source document and the upload date. `Mọi môn` / `Mọi đề` filter it; picking
*20. Sở GD & ĐT Hà Tĩnh* narrowed the list to **6 câu** and put `document_id` in the URL, matching the `(6)` the
document list shows beside that paper. A question carries no date of its own in the API, so the row shows the
date of its source document.

### AC-02 — suggestions
Suggestions are fetched per page in one `POST /questions/suggest-topics` for the ids on screen (batched at 50, the
endpoint's limit) and shown as buttons: full topic path · score · `Từ khóa` / `Tương tự`. `1`/`2`/`3` apply the
first three suggestions of the focused row, `↑`/`↓` move the focus; the row leaves the queue and the counter drops.

### AC-03 — bulk apply
Multi-select → "Gán chuyên đề cho N câu" → TopicPicker → one `POST /questions/bulk` for the whole selection
(verified in the network log: one request per apply, never one per question). Applied in 3, 4, 3, 2, 2, 2 and 2 câu
batches; the counter and the list came back from the server each time (108 → 105 → 101 → 98 → 96 → 94 → 92 → 90,
the last 8 câu one by one from the row's own picker).
The bulk button is disabled when the selection spans several subjects — a topic belongs to one subject and the API
would answer 422.

### AC-05 — coverage
The header counts what is left; the `Đề gốc` list carries the untagged count per paper from
`facets.untagged_documents` (5, 6, 7, 10, … over the 18 papers, plus one question with no document). No count is
shown beside a subject: the subjects facet drops the topic dimension, so it would report every question of the
subject (375) instead of the untagged ones.

### The backlog worked for real
**27 câu tagged**, `109 → 82` remaining. **1** of them was accepted from the top suggestion (`768944f8`, the Zika
question → **Đạo hàm**, 0.43 `similar`, applied with the `1` key); the other **26** were picked by hand in the
TopicPicker. Of the 5 rows I met that had a suggestion at all, I rejected 4: the kNN neighbour puts every
exponential/logarithmic equation and inequality on **Logarit** (the right branch, the wrong node — they belong to
*Phương trình mũ và logarit* / *Bất phương trình mũ và logarit*) and it also fired **Logarit** on
*$\cot x = 1$*, which is a different chapter altogether. Across the whole backlog only **15 of 109** questions had
any candidate. That is the acceptance measurement A-05 asked for, and it is what UOW-03 (ADR-04) answers.

Topics assigned: Các phép toán vectơ (4), Giá trị lớn nhất, nhỏ nhất (5), Đọc đồ thị hàm số (3), Đạo hàm (3),
Phương trình mũ và logarit (2), Bất phương trình mũ và logarit (2), Đường tiệm cận, Quy tắc đếm, Tích phân,
Ứng dụng tích phân tính diện tích, Cực trị của hàm số, Thể tích khối lăng trụ, Phương trình lượng giác cơ bản,
Số đặc trưng của mẫu số liệu ghép nhóm. Every one was read back from `GET /questions/{id}` with
`is_primary: true` and `source: "manual"` (ADR-01). One of them landed on *Số đặc trưng của mẫu số liệu
**không** ghép nhóm* because that node matched the same search text first; it was corrected to the grouped one.

### Checks
- `cd apps/web && pnpm typecheck`, `pnpm lint`, `pnpm test`: **180 passed** in 50 files (6 new).
- `scripts/close_ticket.sh … T-02-01 T-02-02`: exit 0, each with its own verified run of
  `apps/web/src/__tests__/tagging-queue.test.tsx`.
- New tests: the list renders from a body carrying `has_topic: false` first, suggestions are requested for the
  page's ids, clicking a suggestion sends the bulk request with that topic and the row leaves the queue, the `1`
  key applies the focused row's first suggestion, `↓` moves the focus, bulk apply sends one request for several
  ids, and the document filter reaches the body while the facets keep counting every paper.
