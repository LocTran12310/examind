---
feature: review-ux
---

# Demo evidence

## UOW-01 — One state per document, and every question reachable

Run on the live stack (`docker compose up -d --build api`, org `trungtama`, user `admin`), 2026-09-23.
Everything below is read-only except the re-decision of §4, which was put back.

### Checks

| Check | Result |
| --- | --- |
| `make lint-api` (ruff + lint-imports) | 4 contracts kept, 0 broken |
| `./scripts/verify.sh apps/api/tests` | **480 passed, 1 skipped** (3:17) |
| `scripts/close_ticket.sh … T-01-01` / `T-01-02` | exit 0, each with its own verified test run |

### 1. One state per document (AC-01)

`POST /review/documents/search {"limit": 50}` → the 18 papers, each with `review_state` and `pending` next to
the counts it already returned (`counts` and `spot_pending` are unchanged):

| Document | review_state | pending | total | auto_approved | needs_review | approved | spot_pending |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 20. Sở GD & ĐT Hà Tĩnh | done | 0 | 22 | 0 | 0 | 22 | 0 |
| 19. Sở GD & ĐT Bà Rịa - Vũng Tàu | done | 0 | 22 | 0 | 0 | 22 | 0 |
| 18. Huyện Cẩm Xuyên - Hà Tĩnh | done | 0 | 22 | 21 | 0 | 1 | 0 |
| 17. CHUYÊN VINH - NA (Lần 1) | pending | 1 | 22 | 22 | 0 | 0 | 1 |
| 16. SỞ BẮC NINH - KSCL | pending | 6 | 22 | 17 | 5 | 0 | 1 |
| 15. CHUYÊN ĐHKHTN - HCM (Lần 1) | pending | 12 | 22 | 11 | 11 | 0 | 1 |
| 14. SỞ GIÁO DỤC YÊN BÁI | pending | 1 | 22 | 22 | 0 | 0 | 1 |
| 13. CHUYÊN PHAN BỘI CHÂU - NGHỆ AN | pending | 3 | 22 | 20 | 2 | 0 | 1 |
| 12. CHUYÊN VĨNH PHÚC (Lần 1) | pending | 1 | 22 | 22 | 0 | 0 | 1 |
| 11. SỞ GIÁO DỤC NINH BÌNH | pending | 1 | 22 | 22 | 0 | 0 | 1 |
| 10. THPT TRIỆU QUANG PHỤC - HƯNG YÊN | pending | 1 | 22 | 22 | 0 | 0 | 1 |
| 09. THPT THUẬN THÀNH 1-2 - BẮC NINH | pending | 1 | 22 | 22 | 0 | 0 | 1 |
| 08. THPT VĂN GIANG - HƯNG YÊN | pending | 1 | 22 | 22 | 0 | 0 | 1 |
| 07. THCS-THPT NGUYỄN KHUYẾN - TPHCM | pending | 2 | 22 | 21 | 1 | 0 | 1 |
| 6. THPT Thạch Thành 1 - Thanh Hóa (Lần 1) | pending | 1 | 22 | 22 | 0 | 0 | 1 |
| 3. Lê Thánh Tông – TP HCM | pending | 1 | 22 | 22 | 0 | 0 | 1 |
| 2. THPT Lương Tài 2 – Bắc Ninh | pending | 1 | 22 | 22 | 0 | 0 | 1 |
| 1. THPT Quế Võ 1 – Bắc Ninh | pending | 2 | 22 | 20 | 1 | 1 | 1 |

Fifteen papers still carry work, and for thirteen of them the only thing left is the one question the check
sample drew — which is exactly what the owner could not see behind six badges.

### 2. The state is an ordinary search column (AC-01)

| Call | Result |
| --- | --- |
| `filters: {review_state: {value: "pending"}}` | **15** documents, `pending` 12, 6, 3, 2, 2, 1×10 |
| `filters: {review_state: {value: "done"}}` | **3** documents (20., 19., 18.) |
| `sort: [{field: "pending", desc: true}]` | 15. CHUYÊN ĐHKHTN first (12) |
| `filters: {review_state: {value: "xong"}}` | **422** `bad_filter` — `Giá trị không hợp lệ: xong` |

### 3. A document's questions by state (AC-03)

`POST /review/documents/6a3e4540…/questions/search` (15. CHUYÊN ĐHKHTN - HCM):

| state | total | statuses |
| --- | ---: | --- |
| `pending` (default) | 12 | 11 needs_review + 1 auto_approved drawn for the check sample |
| `approved` | 10 | the 10 auto_approved the sample did not draw |
| `rejected` | 0 | — |
| `duplicate` | 0 | — |
| `all` | 22 | 12 + 10 — the states partition the document |

The first pending row is *Câu 1*, group `đáp án không khớp bảng đáp án`; an approved row carries no group.
`{"state": "xem"}` → **422** `bad_filter`. `GET /review/documents/{id}/queue` is untouched.

### 4. A re-decision moves the counts (AC-04)

On *20. Sở GD & ĐT Hà Tĩnh* (`done`, 22/22 approved), question *Câu 1* through `POST /questions/bulk`:

| Step | review_state | pending | counts |
| --- | --- | ---: | --- |
| before | done | 0 | approved 22 |
| `set: {status: "needs_review"}` | pending | 1 | approved 21, needs_review 1 — and the question is back in `state=pending` |
| `set: {status: "rejected"}` | done | 0 | approved 21, rejected 1 — it moves to `state=rejected` |
| `set: {status: "approved"}` | done | 0 | approved 22 — as it started |

The row was then put back byte for byte (`reviewed_by`, `reviewed_at`, `updated_at` restored to the values
recorded before the demo); the whole list compares equal to the reading of §1. The two `bulk` entries the
review log kept are the ordinary audit trail of a status change (A-05).

## UOW-03 — The exam states its own weighting

Run on the live stack (`docker compose up -d --build web`, org `trungtama`, user `admin`), 2026-09-23.
Read-only: no exam, question or setting was written.

### Checks

| Check | Result |
| --- | --- |
| `pnpm typecheck` | clean |
| `NODE_OPTIONS=--max-old-space-size=6144 pnpm lint` | **ESLint: No issues found** |
| `pnpm test` | **191 passed** (51 files), 4 of them new in `src/__tests__/exam-builder.test.tsx` |
| `scripts/close_ticket.sh … T-03-01` | exit 0 |

### 1. What the strip says (AC-06)

"Thang điểm của đề" sits at the top of the exam screen, above "Ma trận đề": a row per part with the number of
questions, the points per question in force and the part's total, a "Cả đề" row with the raw total, then one
sentence about the scale.

*Sở GD&ĐT Hà Tĩnh · Thi thử · 2024-2025* (22 questions, built from a document):

| Phần | Số câu | Điểm/câu | Tổng phần |
| --- | ---: | ---: | ---: |
| Phần I — Trắc nghiệm | 12 | 0,25 | 3 |
| Phần II — Đúng/Sai | 4 | 1 | 4 |
| Phần III — Trả lời ngắn | 6 | 0,5 | 3 |
| **Cả đề** | **22** | tổng thô | **10** |

> Tổng thô **10** điểm — đã đúng thang 10, không phải quy đổi.

The two other document exams (Bà Rịa - Vũng Tàu, Ninh Bình) carry the same 22 questions and the same 10 points.

### 2. A paper that is not already the scale

*Kiểm tra 15p - Hàm số bậc 2* (10 questions, all Trắc nghiệm):

| Phần | Số câu | Điểm/câu | Tổng phần |
| --- | ---: | ---: | ---: |
| Phần I — Trắc nghiệm | 10 | 0,25 | 2,5 |
| **Cả đề** | **10** | tổng thô | **2,5** |

> Tổng thô **2,5** điểm, quy về thang **10**: mỗi điểm thô thành **4** điểm (10 ÷ 2,5).

The 10-point paper gets the plain sentence, the 2,5-point paper the conversion — the confusing "×1" case never
appears.

### 3. A question worth something else than its type default

No live exam has one, so the case was shown by rewriting the exam payload in the browser (a client-side
response rewrite, nothing sent to the API): question 3 of the Hà Tĩnh paper at 1 instead of 0,25.

- Phần I reads `0,25 (có câu khác)` and its total moves to 3,75; Cả đề to 10,75, with the conversion
  "mỗi điểm thô thành 0,93 điểm (10 ÷ 10,75)".
- An amber block names it: **1 câu lệch điểm mặc định** — "Điểm của câu đã sửa riêng; đổi điểm mặc định của
  loại sẽ ghi đè lại: *Câu 3: 1 thay vì 0,25*".
- The link jumps to that question's `điểm` input in "Câu hỏi trong đề" (verified: the page scrolled to the
  input holding 1).

The same case is covered by the unit test `a question worth something else than its type default is named`.

### 4. Where the numbers are edited

The strip does not own any input. It links to the two places that already do: "Sửa điểm mặc định theo loại" and
"Điểm mặc định theo loại câu" → the per-type panel, "Câu hỏi trong đề" → the per-question `điểm` inputs. The
per-type panel gained one sentence, because the API overwrites every question of that type when a default
changes: *"Đổi ở đây sẽ áp lại cho mọi câu cùng loại trong đề, kể cả câu đã sửa điểm riêng."*

### 5. Widths and themes

Checked at 1440×900 and 375×812, dark and light. At 375 px the exam screen's two columns were clipping their
content (the questions table's intrinsic width pushed the grid item to 406 px inside a 375 px viewport); the two
column wrappers now carry `min-w-0`, so the whole strip — including "Tổng phần" — is on screen without a
sideways scroll. No API call, no endpoint and no stored value changed (A-04).

## UOW-02 — The review list and page a teacher can read

Run on the live stack (`docker compose up -d --build web`, org `trungtama`, user `admin`), 2026-09-23, in a
real browser at 1440×900 and 390×844. Everything below is read-only except the edit and re-decision of §4,
which were put back (see §6).

### Checks

| Check | Result |
| --- | --- |
| `pnpm typecheck` | clean |
| `NODE_OPTIONS=--max-old-space-size=6144 pnpm lint` | **No issues found** |
| `pnpm test` (vitest) | **191 passed** in 51 files (185 before: the list's three state cases replace one, plus four on the document page) |
| `scripts/close_ticket.sh … T-02-01` / `T-02-02` | exit 0, each with its own verified test run |

### 1. One state per document, filterable from the column (AC-01)

`/org/review` opens on the papers that still need work: the URL carries `?review_state=pending` and the body
sends `filters: {review_state: {value: "pending"}}` — **15 of the 18 papers**, the three finished ones out of
the way. The old "Tình trạng" column with up to six badges is one "Trạng thái" column:

| Đề | Trạng thái | Tiến độ | | |
| --- | --- | ---: | --- | --- |
| 17. CHUYÊN VINH - NA (Lần 1) | `Cần xem` · còn 1 câu · Chi tiết | 95% | — Chưa giao — | Duyệt 1 câu |
| 16. SỞ BẮC NINH - KSCL | `Cần xem` · còn 6 câu · Chi tiết | 73% | — Chưa giao — | Duyệt 6 câu |
| 15. CHUYÊN ĐHKHTN - HCM (Lần 1) | `Cần xem` · còn 12 câu · Chi tiết | 45% | — Chưa giao — | Duyệt 12 câu |

The header filter is an ordinary select: choosing **Xong** writes `review_state=done` to the URL and to the
body and leaves the three finished papers; the header is sortable on `review_state`. The whole table now fits
1440 px (1150 px of content in 1150 px of room) — the filename wraps inside its column instead of pushing
"Người duyệt" and the action link off screen.

### 2. The counts are one click away, and the sample explains itself (AC-02)

"Chi tiết" opens a popover with the six counts the column used to carry —
`Tự duyệt 10 · Cần xem 11 · Mẫu kiểm chứng 1 · Đã duyệt 1` — and the sentence that names it. The screen itself
says it under the title, so it is readable without opening anything:

> Chỉ những câu cần mắt người mới vào hàng đợi. Mẫu kiểm chứng là 5% số câu hệ thống tự duyệt, rút ngẫu nhiên
> để bắt lỗi máy duyệt sai.

"Kiểm tra ngẫu nhiên" is gone from both screens; the queue card calls the same group "Mẫu kiểm chứng" (ADR-03).

### 3. The document page: a state filter over the queue (AC-03, AC-05)

*15. CHUYÊN ĐHKHTN - HCM* opens on **Cần xem** — the keyboard queue, unchanged: counter `1/12`, the group badge,
the legend `Enter duyệt + câu tiếp · 1–4 chọn đáp án · T chuyên đề · E sửa · X loại · S bỏ qua · J / K câu sau /
trước · còn 12 câu`. Above it: `Hiển thị câu: Cần xem | Đã duyệt | Đã loại | Trùng | Tất cả`, in the URL as
`?state=…`, sent as the endpoint's `state`.

**Đã duyệt** lists the **10** questions the sample did not draw, each naming its own state
(`Câu 2 · Phần 1 · Tự duyệt`) and each saying what its buttons will do:
`Sửa nội dung câu hỏi` · `Duyệt — chuyển sang Đã duyệt` · `Loại — chuyển sang Đã loại` · `Trả lại — chuyển sang Cần xem`.

### 4. Correct an approved question and take the approval back (AC-04)

On *Câu 2* (`ec2e1d85…`, `auto_approved`), from the Đã duyệt list:

| Step | Result |
| --- | --- |
| `Sửa nội dung câu hỏi` | the full `QuestionForm` opens in place, prefilled, with the live preview |
| stem edited, `Lưu câu hỏi` | `PATCH /questions/{id}` → "Đã lưu câu hỏi." |
| `Trả lại — chuyển sang Cần xem` | `POST /questions/bulk {set: {status: "needs_review"}}` → "Đã chuyển câu hỏi sang "Cần xem"." |

The counts followed without a reload: the page header went from `Tự duyệt 11 · Cần xem 11 · Đã duyệt 0 · còn 12
câu` to `Tự duyệt 10 · Cần xem 12 · Đã duyệt 0 · còn 13 câu`, the Đã duyệt list from 10 rows to 9.

### 5. …and the list follows (AC-01, AC-04)

Back on `/org/review`: *15. CHUYÊN ĐHKHTN* read `Cần xem · còn 13 câu · 41% · Duyệt 13 câu` — the state, the
count and the progress all moved with the decision.

### 6. Put back

The stem was restored byte for byte through `PATCH /questions/{id}` (229 characters, compared equal), and the
status through `POST /questions/bulk` — the feature's own command. The list compares equal to the reading of
UOW-01 §1: 18 documents, **15 `pending` / 3 `done`**, pending 12, 6, 3, 2, 2, 1×10, and *15. CHUYÊN ĐHKHTN* back
at `pending` / 12 / progress 0.45.

Two differences remain on that one question, both invisible in the list and both recorded here rather than
hidden: its status is `approved` instead of `auto_approved` (the API has no command that writes `auto_approved`
— ADR-02 gives `bulk` three statuses — and a direct database write was not permitted), so the popover reads
`Tự duyệt 10 · Đã duyệt 1` where it read `Tự duyệt 11 · Đã duyệt 0`; and `answer_source` is `manual` where the
21 siblings are `inline`, because saving the form resubmits the answer. Nothing else moved.
