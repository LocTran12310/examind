---
feature: 2026092303-review-ux
environments: [local]
viewports: [desktop, mobile]
---

# Verification — Review UX

Signed in as an org admin. The live bank holds the 18 official papers: 15 still need work, 3 are finished, and
the three exams built from documents are worth 10 points each.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert |
|---|---|---|---|---|---|
| S1 | The list opens on the papers that still need work, one state each | `/org/review` | `settle 2500` | AC-01 | `text=Cần xem`; `text=còn`; `no-text=Không tải được` |
| S2 | The counts and the sample's explanation sit behind "Chi tiết" | `/org/review` | `settle 2500; click text=Chi tiết >> nth=0; settle 800` | AC-01, AC-02 | `text=Mẫu kiểm chứng`; `text=5%`; `no-text=Kiểm tra ngẫu nhiên` |
| S3 | A paper opens on its pending queue | `/org/review` | `settle 2500; click a[href^="/org/review/"]:not([href$="/untagged"]) >> nth=0; settle 2500` | AC-03 | `text=Cần xem`; `text=Duyệt (Enter)` |
| S4 | The approved questions of a paper can be read back and re-decided | `/org/review?filename=%C4%90HKHTN` | `settle 2500; click a[href^="/org/review/"]:not([href$="/untagged"]) >> nth=0; settle 2500; click button:has-text("Đã duyệt"); settle 2500` | AC-03, AC-05 | `text=Trả lại`; `no-text=Không tải được` |
| S5 | The exam states what each part is worth and what the paper is worth | `/org/exams` | `settle 2500; click text=Thi thử >> nth=0; settle 1500; click text=Soạn đề & giao bài; settle 3000; scroll text=Thang điểm của đề; settle 500` | AC-06 | `text=Thang điểm của đề`; `text=Cả đề`; `text=thang 10` |

## Not verified here

AC-04 (correct and re-decide a question) changes live data: the walk was done by hand during UOW-02 — edit a stem,
send it back to "Cần xem", watch the header and the list follow — and then put back. Repeating it on every run
would write to the organisation on every verification, so it stays covered by
`apps/web/src/__tests__/review-document.test.tsx` (the re-decision sends `needs_review` and refetches),
`apps/api/tests/test_review_queue.py::test_a_re_decision_moves_the_counts_and_the_state` and the record in
`07-demo-evidence.md`.

## Notes

S2 asserts `no-text=Kiểm tra ngẫu nhiên`: the rename is the point, and a screenshot of the new label proves
nothing if the old one is still on the page somewhere else. Assertions name text from the page body, not the
sidebar, because the sidebar is collapsed at 390 px.

The step selectors exclude what the sidebar offers under the same prefix: the first `a[href^="/org/review/"]` on
the page is the nav link to "Chưa gắn chuyên đề", and a run that photographs that screen is green on the wrong
page. The exam opens through its title dialog, which is how a teacher reaches it. S4 filters the list to one paper by
filename because "the first row" is whichever paper sorts first, and most of them have nothing approved yet —
a step that lands on an empty state asserts nothing about reading decisions back. It clicks
`button:has-text("Đã duyệt")` rather than the text, because the document's own subtitle already reads
"Đã duyệt 1" and a click on that does nothing while looking right.
