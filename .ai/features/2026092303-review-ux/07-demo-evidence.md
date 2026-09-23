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
