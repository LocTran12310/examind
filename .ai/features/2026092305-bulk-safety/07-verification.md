---
feature: 2026092305-bulk-safety
environments: [local]
viewports: [desktop, mobile]
---

# Verification — Undo for the bulk bar, and a way back from a detail page

Signed in as an org admin, against the owner's real bank: 357 Toán questions and 21 nobody has classified.

**The run leaves the bank as it found it.** S2 makes a real edit — one question's mức độ — and S3 takes it back
out of "Thay đổi gần đây", which is the feature verifying itself. Every step starts from a fresh page load, so
this pairing is the only way a walk that ends at a toast can still be net zero. The residue is `review_events`
rows, append-only by design and exactly what S4 and S5 then read; nothing else on the stack is written.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert |
|---|---|---|---|---|---|
| S1 | A bulk edit's toast carries the way back, and each action names how many it will change | `/org/bank` | `settle 3500; click [aria-label="Chọn câu"] >> nth=0; settle 500; click button:has-text("Mức độ"); settle 800` | AC-06 | `text=Đặt mức độ cho 1 câu`; `text=Vận dụng cao` |
| S2 | The edit reports what it did and offers "Hoàn tác" for that very edit | `/org/bank` | `settle 3500; click [aria-label="Chọn câu"] >> nth=0; settle 500; click button:has-text("Mức độ"); settle 800; click [role=menuitem]:has-text("Vận dụng cao"); settle 2500` | AC-01 | `text=Đã đặt mức độ Vận dụng cao: 1 câu`; `count button:has-text("Hoàn tác") = 1`; `no-text=Có lỗi xảy ra` |
| S3 | A change found later is taken back from the list, and it restores what the edit touched | `/org/bank` | `settle 3500; click button:has-text("Thay đổi gần đây"); settle 3000; click [data-testid=recent-changes] button:has-text("Hoàn tác") >> nth=0; settle 3000` | AC-01, AC-03 | `text=Đã hoàn tác 1 câu`; `no-text=Có lỗi xảy ra` |
| S4 | "Thay đổi gần đây" says when, who, what changed and how many | `/org/bank` | `settle 3500; click button:has-text("Thay đổi gần đây"); settle 3000` | AC-03 | `count [data-testid=recent-changes] = 1`; `text=Người sửa`; `text=Đã đổi`; `text=Số câu`; `text=Sửa hàng loạt`; `text=Mức độ` |
| S5 | The undo is a change of its own, and the edit it took back says so | `/org/bank` | `settle 3500; click button:has-text("Thay đổi gần đây"); settle 3000` | AC-04, AC-05 | `text=Lượt sửa này đã được hoàn tác`; `text=Đây đã là một lần hoàn tác` |
| S6 | The assignment report has a way back | `/org/assignments/343ab1a2-169c-4fa3-8a56-4f0729f45bd8` | `settle 3000` | AC-07 | `text=← Đề thi`; `text=Báo cáo bài giao`; `no-text=Không tải được` |
| S7 | So does the new-question form | `/org/bank/new` | `settle 3000` | AC-07 | `text=← Ngân hàng câu hỏi`; `no-text=Không tải được` |

## Not verified here

- **AC-02 (all or nothing).** Making it fail needs a question of the batch to be deleted between the edit and
  the undo — a deletion on the owner's bank, which no verification run may do. Covered by
  `apps/api/tests/unit/test_bank_handlers.py` (a batch that lost a question refuses whole) and
  `apps/api/tests/test_bank_api.py::test_undo_puts_a_bulk_edit_back_and_only_once`.
- **AC-05, the aged batch.** The 7-day reason cannot be produced without ageing rows in the database. The HTTP
  test ages a batch with SQL and asserts the refusal; S5 verifies the two reasons that occur naturally.
- **AC-07, the attempt result.** The one assignment on this stack has nothing submitted (`0/1`), so there is no
  attempt to open. Covered by `apps/web/src/__tests__/result.test.tsx`, which asserts the link for the teacher,
  for the student and on the failed-load branch.

## Notes

S1 and S2 repeat their interaction because the runner starts every step from a fresh page load: a step cannot
inherit the one before it. That is also why the undo is pressed in the list rather than in the toast — a step
that stopped at the toast would leave its edit standing, and the first run of this spec did exactly that, one
question left at "Vận dụng cao" per viewport. Pressing it from "Thay đổi gần đây" instead takes back the edit
S2 left, so the walk is net zero per viewport, and it verifies the case the feature exists for: the mistake
noticed after the toast is gone.

S2 asserts `count button:has-text("Hoàn tác") = 1` rather than the text: "Hoàn tác" is also the label of the
undo button on every row of "Thay đổi gần đây", so a bare text assertion would pass on a screen where the toast
had no button at all. Pressing *that* button — same handler, same request as the row's — is covered by
`apps/web/src/__tests__/bank-bulk.test.tsx`, which walks the edit, the click and the body it sends.

The first run of this spec also caught a layout defect the tests could not: six columns did not fit the sheet,
so at 1440 px the column holding the undo button — and the sentence saying why a row has none — was clipped off
the right edge. The sheet is wider now and S4's screenshot shows a whole row. At 390 px the table still scrolls
sideways to reach that column; pinning it there was tried and reverted, because a 176 px column pinned over a
390 px row draws on top of the two columns beside it. A phone-sized layout for this list is a separate piece of
work, and the honest record is that on a phone the way back is a sideways scroll away.

S5 asserts the two sentences the API writes for `already_undone` and `is_undo`. They are there because S3 ran:
the row the undo took back now reads one, the undo's own row reads the other. Nothing client-side decides this —
both come back from `POST /question-events/search`, which is the point of AC-04.

S6 and S7 assert `← ` with the label, not the label alone: "Đề thi" is also part of the sidebar's
"Đề thi & giao bài" and "Ngân hàng câu hỏi" is a sidebar item too, so the arrow is what distinguishes the back
link from the navigation. The sidebar is collapsed at 390 px, which would make a bare-label assertion pass on
one viewport and fail on the other for a reason that has nothing to do with the feature.
