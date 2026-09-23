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
