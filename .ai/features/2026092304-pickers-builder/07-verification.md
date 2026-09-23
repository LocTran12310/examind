---
feature: 2026092304-pickers-builder
environments: [local]
viewports: [desktop, mobile]
---

# Verification — Pickers and exam builder

Signed in as an org admin. The live bank holds 377 questions of one subject (Toán) plus 21 nobody has
classified, 40 of which still have no topic; the taxonomy has 71 topics, 20 of them without a single usable
question. The exam `Kiểm tra 15p - Hàm số bậc 2` is empty and its matrix has one row, so it is the exam the
refusals are demonstrated on — a refused generate writes nothing.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert |
|---|---|---|---|---|---|
| S1 | The matrix row says how many questions its topic holds | `/org/exams/be4eddb5-7c90-4611-a6e0-254cf665cf28` | `settle 3000; scroll text=Ma trận đề; settle 500` | AC-02 | `text=Ứng dụng đạo hàm để khảo sát hàm số`; `text=90 câu`; `no-text=Không tải được` |
| S2 | The picker opens on the topic that row already points at, applying nothing | `/org/exams/be4eddb5-7c90-4611-a6e0-254cf665cf28` | `settle 3000; click [data-testid=blueprint] button:has-text("Ứng dụng đạo hàm"); settle 1500` | AC-01 | `count [data-testid=topic-picker] [role=treeitem][aria-selected="true"] = 1`; `count [data-testid=topic-picker] [role=treeitem][aria-selected="true"]:has-text("Ứng dụng đạo hàm để khảo sát hàm số") = 1` |
| S3 | Beside each topic is its own number of questions, and a topic with none reads 0 | `/org/exams/be4eddb5-7c90-4611-a6e0-254cf665cf28` | `settle 3000; click [data-testid=blueprint] button:has-text("Ứng dụng đạo hàm"); settle 1500; fill [aria-label="Tìm chuyên đề"] = conic; settle 800` | AC-02 | `text=Ba đường conic`; `count [role=treeitem]:has-text("Ba đường conic") span[title="0 câu hỏi"] = 1` |
| S4 | A row on that topic is marked before anything is generated | `/org/exams/be4eddb5-7c90-4611-a6e0-254cf665cf28` | `settle 3000; click [data-testid=blueprint] button:has-text("Ứng dụng đạo hàm"); settle 1500; fill [aria-label="Tìm chuyên đề"] = conic; settle 800; click [role=treeitem]:has-text("Ba đường conic"); settle 800; scroll text=Ma trận đề; settle 500` | AC-02, AC-06 | `text=0 câu`; `text=chưa có câu hỏi nào dùng được` |
| S5 | Generating is refused, naming the row, the topic and what it holds | `/org/exams/be4eddb5-7c90-4611-a6e0-254cf665cf28` | `settle 3000; click [data-testid=blueprint] button:has-text("Ứng dụng đạo hàm"); settle 1500; fill [aria-label="Tìm chuyên đề"] = conic; settle 800; click [role=treeitem]:has-text("Ba đường conic"); settle 800; click button:has-text("Tạo đề theo ma trận"); settle 2500; scroll [data-testid=blueprint-refusal]; settle 500` | AC-06 | `count [data-testid=blueprint-refusal] = 1`; `text=Dòng 1: chuyên đề`; `text=Ba đường conic`; `text=không có câu hỏi nào dùng được`; `text=Chưa có câu nào` |
| S6 | "Gán theo gợi ý" counts per question, not per selection | `/org/review/untagged` | `settle 4000; click [aria-label="Chọn cả trang"]; settle 1000` | AC-03 | `text=Gán theo gợi ý (`; `text=Bỏ chọn`; `no-text=Không tải được` |
| S7 | The paper filter is a list that scrolls inside the dropdown, each paper with what it still holds | `/org/review/untagged` | `settle 4000; click [aria-label="Đề gốc"]; settle 1200` | AC-04 | `count [data-testid=option-list] = 1`; `text=Mọi đề` |
| S8 | A subject the questions' topics contradict is refused whole and named | `/org/bank?subject_id=80e44dce-c2b0-45a6-bcf1-7ab2d14aa1d4&topic_id=db91af69-ddc1-4a3c-b03e-6c5508f9afe5` | `settle 3500; click [aria-label="Chọn cả trang"]; settle 800; click button:has-text("Môn"); settle 800; click [role=menuitem]:has-text("Vật lý"); settle 2500` | AC-05 | `count [data-testid=subject-conflict] = 1`; `text=Chưa đổi được môn`; `text=đang có chuyên đề thuộc môn khác`; `no-text=Đã đặt môn` |
| S9 | "Đổi câu" offers the system's pick and a search of the bank | `/org/exams/b9e582b5-1f95-41e6-9cf5-343e51c658ee` | `settle 3500; scroll text=Câu hỏi trong đề; settle 500; click button:has-text("Đổi câu") >> nth=0; settle 1500` | AC-07 | `count [data-testid=swap-dialog] = 1`; `text=Để hệ thống chọn`; `text=hoặc tìm trong ngân hàng và tự chọn`; `text=câu thay thế giữ nguyên vị trí và số điểm này` |
| S10 | The search inside "Đổi câu" returns questions of the bank to choose from | `/org/exams/b9e582b5-1f95-41e6-9cf5-343e51c658ee` | `settle 3500; scroll text=Câu hỏi trong đề; settle 500; click button:has-text("Đổi câu") >> nth=0; settle 1500; fill [aria-label="Tìm nội dung"] = ham so; settle 3000` | AC-07 | `count [data-testid=swap-results] = 1` |

## Not verified here

Four claims of this feature write to the organisation, and a verification that runs on every commit must not
tag questions, change subjects or rebuild exams each time. They are covered by tests and by the live walk
recorded in `07-demo-evidence.md`:

- **AC-03, applying the suggestions.** The walk took the backlog from 102 untagged questions to 40 — 62 tagged
  in four clicks. Covered by `apps/web/src/__tests__/tagging-queue.test.tsx` ("«Gán theo gợi ý» sends every
  row's own suggestion in one request and names what it did not do") and
  `apps/api/tests/unit/test_bank_handlers.py::test_bulk_topics_applies_each_pair_and_names_what_it_skipped`.
  S6 verifies the accounting that decides what would be sent — how many of the selected rows have a suggestion —
  without sending it.
- **AC-04, the second page of papers.** Only 8 papers still hold untagged questions, so the list on screen has
  no end to reach; the paging itself is covered by `tagging-queue.test.tsx` ("the document filter scrolls and
  asks for the next page at the end of the list"). S7 verifies what is on screen: the list is the scrolling
  container and not a dropdown that grows past the viewport.
- **AC-05, setting a subject or a grade.** Covered by `bank-bulk.test.tsx` ("sets a subject and a grade for the
  selection through the same bulk command") and `apps/api/tests/test_bank_api.py::test_bulk_sets_subject_and_grade_and_refuses_a_topic_of_another_subject`.
  S8 verifies the guard, which is the part that was missing and which writes nothing when it fires.
- **AC-07, completing the swap.** Covered by `exam-builder.test.tsx` ("a chosen question takes the place, the
  number and the points of the one it replaces" and "the automatic replacement is still one click"). S9 and S10
  verify that both routes are offered and that the bank search answers.

## Notes

The refusals are demonstrated on the empty exam `Kiểm tra 15p - Hàm số bậc 2`, never on the three papers built
from documents. Both are safe by construction — the API refuses before it saves, which was checked directly
(`POST /exams/{id}/blueprint` → 422 `empty_topic`, `POST /questions/bulk` → 422 `subject_topic_conflict`, and the
exam still reads 0 questions with its original matrix row afterwards) — but a step that fails for an unforeseen
reason should still not be able to rewrite a paper the owner cares about.

S2 asserts the selected row **by its name**, not merely that one row is selected: without a suggestion to land
on, the picker selects its first row anyway, so `aria-selected = 1` alone would be green on a picker that
ignores `initial` entirely. S3 asserts the number through the `title` attribute rather than the text "0",
because a bare `text=0` matches any number on the page. That the number is questions and not child topics is
what S1's `90 câu` says: that topic has five child topics, so a picker that went back to counting children
would read 5 there and fail the step. S5's last assertion is the exam's own empty state — a refusal that had
quietly generated something anyway would replace it with a list of questions.

S5 and S8 are the two steps that rely on `console_ignore` in `.ai/aidlc.yaml`: both make a request the server
is supposed to refuse, and the browser logs a `console.error` for any non-2xx fetch, so the run's
`console_errors` signal fired on a step that had passed every assertion. The filter names that one status and
nothing else — an uncaught exception still fails a step — and it is the reason a refusal can be verified here
at all instead of being written off as unverifiable.

Assertions name text from the page body rather than the sidebar, which is collapsed at 390 px, and the two
buttons are reached with `button:has-text(...)` rather than bare text: "Môn" is also the label of a filter and
of a table column, and "Đổi câu" is the dialog's own title once it is open.
