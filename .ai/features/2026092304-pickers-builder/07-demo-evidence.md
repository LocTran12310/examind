---
feature: pickers-builder
---

# Demo evidence

Responses quoted below are real calls against the running stack (`docker compose up -d --build api`,
`http://localhost:8088`), organisation `trungtama`, signed in as `admin`. Unicode escapes from `curl` are written
back as text for readability; nothing else is edited.

## UOW-01 — Bulk by suggestion, subject and grade, and a builder that refuses an empty topic

Tickets T-01-01, T-01-02, T-01-03 (all `done`). Suite: `./scripts/verify.sh apps/api/tests` →
**486 passed, 1 skipped** (480 before this UoW); `make lint-api` green (ruff + 4 import contracts kept).

### 1. `POST /questions/bulk/topics` — a page of the queue in one request (AC-03, ADR-02)

Eight pairs, five different topics, one request. The bank had 107 questions with no topic at the time.

```json
{
  "updated": 5,
  "skipped": [
    {"question_id": "789ae65f-c78a-45c2-a9f9-451d3a4533cc", "topic_id": "db91af69-ddc1-4a3c-b03e-6c5508f9afe5",
     "reason": "other_org", "message": "Câu hỏi của đơn vị khác"},
    {"question_id": "00000000-0000-4000-8000-000000000001", "topic_id": "db91af69-ddc1-4a3c-b03e-6c5508f9afe5",
     "reason": "unknown_question", "message": "Không tìm thấy câu hỏi"},
    {"question_id": "a4f0e62c-0344-4fd4-a96a-1c66f6cd2e73", "topic_id": "00000000-0000-4000-8000-0000000000ff",
     "reason": "unknown_topic", "message": "Chuyên đề không hợp lệ"}
  ]
}
```

The five that took a topic, and which one (chosen from the untagged backlog; the first is the question's own
top suggestion from `POST /questions/suggest-topics`):

| Question | Topic |
| --- | --- |
| `55c050ff-99e7-4d68-ab56-ab496c6e6f78` | Hàm số bậc hai và đồ thị |
| `16dc8f39-9a63-44e4-814c-07efaa1e0c3a` | Bất phương trình mũ và logarit |
| `4480186b-ee71-486b-9606-682d67d705f2` | Khối đa diện và thể tích |
| `6ee74899-470d-4437-b784-a0aadb1fadfe` | Đọc đồ thị hàm số |
| `cf75f48c-b052-419d-841e-04de5d4696d9` | Ứng dụng đạo hàm để khảo sát hàm số |

The link is primary and manual — a human confirmed it, even when the value came from a suggestion:

```json
[{"id": "088f7e8c-7fb6-4823-bc8c-39548967ce8f", "name": "Khối đa diện và thể tích",
  "is_primary": true, "source": "manual", "score": 1.0}]
```

`has_topic: false` went from 107 to 102. 201 pairs → 422:

```json
{"code": "validation_error", "message": "Tối đa 200 cặp câu hỏi – chuyên đề mỗi lần",
 "details": {"requestId": "…", "fields": {"pairs": "Tối đa 200 cặp câu hỏi – chuyên đề mỗi lần"}}}
```

### 2. `POST /questions/bulk` — subject and grade (AC-05, A-04)

Three questions from the "Chưa phân môn" set (22 at the time): `360992a2-…`, `5f7ca961-…`, `efa7b6ce-…`.

**The rule chosen for the subject / topic conflict: refuse, name the conflict, apply nothing.** The owner
settled this on 2026-09-23 (recorded in `01-assumptions.md` A-04 and in `03-logical-design.md`): a bulk subject
that would leave a question placed in another subject's tree is refused with 422 `subject_topic_conflict`; the
bank never drops a teacher's placement by itself, and the teacher fixes the topic first. The whole bulk is one
transaction, so a conflicting question never leaves the others half-applied. Setting `subject_id` to Vật lý while
the three questions sit in the Toán tree:

```json
{
  "code": "subject_topic_conflict",
  "message": "3 câu đang có chuyên đề thuộc môn khác (Giá trị lớn nhất, nhỏ nhất, Đường tiệm cận, Tính đơn điệu của hàm số). Bỏ hoặc đổi chuyên đề của những câu đó trước khi đổi môn.",
  "details": {"requestId": "…", "fields": {
    "subject_id": "3 câu đang có chuyên đề thuộc môn khác (…). Bỏ hoặc đổi chuyên đề của những câu đó trước khi đổi môn.",
    "conflicts": [
      {"question_id": "360992a2-f25f-41c5-9baf-655d933b8adb", "topic_id": "45808e1c-d8ac-49cf-9c9f-6a16caa0082f", "topic_name": "Giá trị lớn nhất, nhỏ nhất"},
      {"question_id": "5f7ca961-101d-4794-a826-09ae1974de7d", "topic_id": "8ba678c9-b859-4d20-8c3f-28ed67292ace", "topic_name": "Đường tiệm cận"},
      {"question_id": "efa7b6ce-9876-41c7-878e-08ea5ee53902", "topic_id": "a8093cf5-4024-488d-af6b-e5f3e2e315f3", "topic_name": "Tính đơn điệu của hàm số"}
    ]}}
}
```

The subject their topics do belong to, with a grade, in one request — "Chưa phân môn" went 22 → 19:

```json
{"updated": 3}
```

A grade the organisation does not teach is refused exactly as a single edit refuses it:

```json
{"code": "validation_error", "message": "Lớp không hợp lệ",
 "details": {"requestId": "…", "fields": {"grade": "Lớp không hợp lệ"}}}
```

### 3. The blueprint refuses an empty topic (AC-06, A-05)

**What the code did before:** `ApplyBlueprintHandler` drew each row from `bank.pool(...)` — the usable questions
of the organisation whose topic is **anywhere in the row topic's own subtree** (`topics.path <@ <row topic>`),
narrowed by the row's type and difficulty, minus what earlier rows had taken. A row that came up short was
reported in `shortfalls` (`{"row": i, "missing": n}`) and the exam was generated with fewer questions than asked.
There is no "widen to the parent" step anywhere in that path: a row only ever draws from its own subtree.

**What it does now:** before anything is cleared or drawn, each row's topic is measured on its own — what it holds
in the exam's subject, ignoring the row's type and difficulty. A topic that holds nothing usable refuses the whole
generation, naming the row, the topic and the count. A row that can be filled behaves exactly as before, shortfalls
included. On a new exam, row 2 on "Số nguyên tố, ƯCLN và BCNN":

```json
{
  "code": "empty_topic",
  "message": "Dòng 2: chuyên đề “Số nguyên tố, ƯCLN và BCNN” không có câu hỏi nào dùng được (0 câu). Chọn chuyên đề khác hoặc bổ sung câu hỏi cho chuyên đề này.",
  "details": {"requestId": "…", "fields": {"rows": "Dòng 2", "row": 1,
    "topic_id": "f6117ec3-9d42-4503-b551-8b6f7e257b4a", "topic_name": "Số nguyên tố, ƯCLN và BCNN",
    "question_count": 0}}
}
```

Nothing was written: the exam still had 0 questions afterwards. Rows on a topic that holds questions still work,
and a row too narrow for its type or difficulty is still a shortfall, not a refusal:

```json
{"added": 1, "shortfalls": [{"row": 0, "missing": 2}, {"row": 1, "missing": 2}]}
```

### What this demo changed on live data

- **Kept:** the five questions in the table above now have a primary topic (`source: manual`). They came from the
  untagged backlog, which is what the demo asked for.
- **Put back:** `360992a2-…`, `5f7ca961-…`, `efa7b6ce-…` were given subject Toán and grade 12 for the demo and set
  back to no subject / no grade by id afterwards (`update questions set subject_id = null, grade = null where id in (…)`);
  "Chưa phân môn" is 22 again.
- **Put back:** the throwaway exam "Thử ma trận UOW-01" was deleted (`DELETE /api/exams/{id}` → 204).

## UOW-02 — Pickers that start on the suggestion and count questions

Tickets T-02-01, T-02-02, T-02-03 (all `done`). Suite: `cd apps/web && pnpm typecheck && pnpm lint && pnpm test`
→ **198 passed** in 51 files (191 before this UoW; +7 cases). Screens walked in the built stack
(`docker compose up -d --build web`, `http://localhost:8088`), organisation `trungtama`, signed in as `admin`.

### 1. The picker starts on the suggestion and its numbers are questions (AC-01, AC-02, ADR-01)

`TopicPicker` and `TopicTreeSelect` gained `initial` (a topic id: its ancestors open, the row is focused and
scrolled to, **nothing is applied**) and take `counts` from `POST /questions/facets` for the subject in hand.
The count of child topics is gone from both.

**Tagging queue, "Chuyên đề khác…" on a row whose suggestion is "Đại số › Đại số tổ hợp 90% · AI"** — the tree
opened on that topic, focused, with nothing written (`/questions/bulk*` untouched):

```
Số học 3 · Đại số 45 (aria-selected) · Mệnh đề và tập hợp 13 · Bất phương trình bậc nhất hai ẩn 0 ·
Hàm số bậc hai và đồ thị 3 · Phương trình quy về phương trình bậc hai 0 · Đại số tổ hợp 4 (focused) ·
Hàm số lượng giác và phương trình lượng giác 0 · Dãy số, cấp số cộng, cấp số nhân 12 ·
Hàm số mũ và hàm số logarit 13 · Giải tích 94 · Hình học 93 · Thống kê và Xác suất 32
```

The numbers are questions, not children: `Đại số tổ hợp` has 4 questions and 0 child topics; `Đại số` has 6
children and reads 45. A topic known to hold none reads 0 and is muted — `POST /questions/facets`
(`subject_id` = Toán) answers no entry for `Các phép toán vectơ` (`60a52196-…`), and searching "phep toan vecto"
in the picker gives `Hình học 93 · Vectơ 10 · Các phép toán vectơ 0`.

**Review queue, `T` on question `b7890b0c-…`** whose card shows "Tọa độ trong không gian Oxyz": the tree opened
with `Hình học` expanded and that topic focused, counts from the document's subject —
`Số học 3 · Đại số 57 · Giải tích 110 · Hình học 121 · … · Tọa độ trong không gian Oxyz 36 (focused) ·
Thống kê và Xác suất 33`. The question was unchanged afterwards
(`[('Tọa độ trong không gian Oxyz', 'manual')]`), and the keyboard flow (`Enter`/`X`/`S`/`J`/`K`/`1–4`) is intact.

**Where no number is shown, and why.** Counts need the subject in hand. Two pickers have none wired and now show
no number at all rather than a misleading one: the single-question form (`QuestionForm`, a `components/common`
component that may not hold a query hook — its caller would have to pass the counts) and the exam builder's
blueprint row (`BlueprintEditor`, which UOW-03 owns). Both used to print the child count; that number is gone.

### 2. "Gán theo gợi ý" — a page of the queue in one request (AC-03, ADR-02)

The bulk bar gained **"Gán theo gợi ý (N)"**, N being how many of the selection have a suggestion; a selection
spanning subjects no longer blocks it, because each question takes its own topic. One `POST /questions/bulk/topics`
carries the pairs; questions with no suggestion are never sent and are named, as is anything the server skipped.

Three runs on the live backlog, "Chưa gắn chuyên đề" starting at **102**:

| Run | Selection | Request | Answer | Message | Remaining |
| --- | --- | --- | --- | --- | --- |
| 1 | cả trang (20) | 1 × `bulk/topics`, 20 pairs | `{"updated": 20, "skipped": []}` | Đã gán chuyên đề cho 20 câu | 102 → 82 |
| 2 | cả trang (20) | 1 × `bulk/topics`, 20 pairs | `{"updated": 20, "skipped": []}` | Đã gán chuyên đề cho 20 câu | 82 → 62 |
| 3 | cả trang (20) | 1 × `bulk/topics`, 20 pairs | `{"updated": 20, "skipped": []}` | Đã gán chuyên đề cho 20 câu | 62 → 42 |
| 4 | cả trang (20), selected before the model had answered | 1 × `bulk/topics`, **2** pairs | `{"updated": 2, "skipped": []}` | **Đã gán chuyên đề cho 2 câu · 18 câu chưa có gợi ý** | 42 → 40 |

Run 4 is the honest case the assumption asks for: only the two rule-based suggestions existed at that moment, the
bar said "18 câu chưa có gợi ý" **before** the click, the request carried two pairs, and the other eighteen were
left untouched and named. Nothing was skipped by the server in these runs; the skipped reasons are covered by the
unit test (`subject_mismatch` → "1 câu bị bỏ qua (Chuyên đề không thuộc môn của câu hỏi)").

**One change beyond the ticket's wording.** `useBulkTopicsMutation` starts its cache invalidation instead of
awaiting it. The invalidation refreshes the queue's own suggestions query, which the tagging model answers in tens
of seconds; awaited, the toast and the cleared selection arrived that late — the bar claimed 20 selected while no
row was ticked. Started and not awaited, the list still refreshes and the teacher hears the result at once. The
same lag still exists on the older `useBulkUpdateQuestionsMutation` path; it predates this UoW and was left alone.

### 3. The document filter scrolls and pages (AC-04, A-07)

`OptionSelect` gained `onEndReached` / `loadingMore`: the options sit in a bounded, scrolling box inside the
dropdown, and reaching the end asks the page hook for the next page. The tagging queue now loads papers 50 at a
time and keeps what it has loaded, so the list grows instead of being replaced.

Live: the 18 papers fit in one page, so no second request is made today — the dropdown is measurably scrolling
inside itself (`scrollHeight 336 > clientHeight 256`, 12 options: 11 papers that still hold untagged questions,
each with its count, plus "Mọi đề"). The paging itself is covered by
`tagging-queue.test.tsx` ("the document filter scrolls and asks for the next page at the end of the list"), which
serves one paper per page and asserts the second request and that the first paper is still listed afterwards.

### 4. Subject and grade from the bank toolbar (AC-05, A-04)

The bulk bar gained **"Môn"** and **"Lớp"**, both through `POST /questions/bulk` `set`. On the live
"Chưa phân môn" tab (22 questions), with `5f7ca961-…`, `360992a2-…` and `efa7b6ce-…` selected:

- **Môn → Vật lý**: refused, and the refusal is the product behaviour, not a swallowed error. A dialog
  "Chưa đổi được môn" shows the server's message —
  *"3 câu đang có chuyên đề thuộc môn khác (Giá trị lớn nhất, nhỏ nhất, Đường tiệm cận, Tính đơn điệu của hàm số).
  Bỏ hoặc đổi chuyên đề của những câu đó trước khi đổi môn."* — then one row per conflict from
  `details.fields.conflicts`: a link to that question in the bank, its topic, and its stem rendered as the bank
  renders it (question numbers repeat from paper to paper, so the stem is what tells two "Câu 1" apart). It closes
  with what to do: *"Không câu nào bị đổi. Mở từng câu ở trên, bỏ hoặc đổi chuyên đề sang môn mới, rồi đặt lại môn
  cho cả nhóm."* "Chưa phân môn" stayed at 22.
- **Môn → Toán** on the same three: `{"updated": 3}`, toast "Đã đặt môn Toán: 3 câu", and the tab counts followed
  at once — Toán 356 → 359, Chưa phân môn 21 → 18.
- **Lớp → Lớp 12** on the same three: `{"updated": 3}`, toast "Đã đặt Lớp 12: 3 câu".

The topic picker of the same bar now takes its counts from the subject the bank is showing, and only asks for them
when the picker opens.

### What this demo changed on live data

- **Kept (this is what the screen is for):** 62 questions of the untagged backlog were given a primary topic by
  four clicks of "Gán theo gợi ý" — each its own top suggestion, `source: manual`, `is_primary: true`.
  `has_topic: false` went 102 → 82 → 62 → 42 → 40. The first twenty, with the topic each took, are:
  `d945aa50-…` Đại số tổ hợp · `1007d8f9-…` Quan hệ song song trong không gian ·
  `544d80e7-…` Hoán vị, chỉnh hợp, tổ hợp · `7ffb53bc-…` Phương trình đường tròn ·
  `a5f0b3ac-…` Ứng dụng đạo hàm để khảo sát hàm số · `3da71e55-…` Nguyên hàm ·
  `3c6c2531-…` Phương trình đường thẳng trong không gian · `a5f28b53-…` Vectơ ·
  `8fea9657-…` Giới hạn và hàm số liên tục · `b5a8f7bd-…` Tích phân · `0b33c5fb-…` Logarit ·
  `0f6ee681-…` Tọa độ trong không gian Oxyz · `c5d8655e-…` Phương trình mặt phẳng ·
  `fddc0cfe-…` Phương trình mặt cầu · `f84e465c-…` Phương trình đường thẳng trong không gian ·
  `5ac006ec-…` Ứng dụng đạo hàm để khảo sát hàm số · `768944f8-…` Đạo hàm · `811b6b42-…` Logarit ·
  `09531fa1-…` Phương trình đường thẳng trong không gian · `606f225a-…` Ứng dụng đạo hàm để khảo sát hàm số.
  The other forty-two are the rows the queue showed on the three following clicks, in the same
  newest-first order; every one of them is listed in `question_topics` with `source = 'manual'`.
- **Put back:** `5f7ca961-…`, `360992a2-…` and `efa7b6ce-…` were given subject Toán and grade 12 to demonstrate
  the successful path, and set back to no subject / no grade by id afterwards
  (`update questions set subject_id = null, grade = null where id in (…)`). "Chưa phân môn" is 22 again.
- **Unchanged:** the refused "Môn → Vật lý" wrote nothing (checked: "Chưa phân môn" still 22 straight after), and
  opening a picker on a suggestion — in the tagging queue and with `T` in the review queue — wrote nothing
  (`b7890b0c-…` still holds only its own topic).

## UOW-03 — A blueprint that reads well and a swap the teacher controls

Tickets T-03-01, T-03-02 (both `done`). Suite: `cd apps/web && pnpm typecheck && pnpm lint && pnpm test`
→ **203 passed** in 51 files (198 before this UoW; +5 cases, all in `exam-builder.test.tsx`). Screens walked in the
built stack (`docker compose up -d --build web`, `http://localhost:8088`), organisation `trungtama`, signed in as
`admin`, on an exam created for the walk and deleted afterwards (see "What this demo changed on live data").

### 1. The matrix row is one line, and says what its topic holds (AC-02 for this screen, AC-06)

The row was a `flex flex-wrap`: at the width the builder actually gets it wrapped onto a second line with the `×`
stranded. It is now a grid — one line from `lg` up, two deliberate columns below it:

| Width | What the row does | Measured |
| --- | --- | --- |
| 1440 px | one line: chuyên đề · tag · loại · mức độ · số câu · ✕ | six cells, tops 336–338, row 50 px high, topic cell 157 px |
| 1024 px | the same one line, wider (the page is one column here) | tops 272–274, topic cell 216 px |
| 390 px | stacks: chuyên đề full width, then tag+loại, mức độ+số câu, then "✕ Xóa dòng" at the right | five rows, 190 px high, `document.scrollWidth` 390 — no sideways scroll |

The topic button names the topic itself (`Nguyên hàm`) and carries the whole path in its tooltip
(`Giải tích › Nguyên hàm`) — the line is narrow, and the path is what the picker shows anyway.

**The count is questions, and it is on the row.** `BlueprintEditor` now takes the counts UOW-02 left unwired:
`useBlueprintEditor` asks `POST /questions/facets` for the exam's subject, and — for an exam that has no subject of
its own, which is every exam created by hand — for the whole bank, because the tree it offers is the whole
taxonomy too (`useTopicCountsQuery(..., allSubjects)`); the number then covers exactly what is listed. Live, the
picker opened on `Số học 3 · Đại số 57 · Giải tích 118 · Hình học 126 · Thống kê và Xác suất 34`, and
`nguyen ham` gave `Giải tích 118 › Nguyên hàm 3 › Nguyên hàm cơ bản 0`. Picking `Nguyên hàm` wrote
**`Nguyên hàm · 3 câu`** on the row.

**An empty topic is named before generating.** On the second row, `so nguyen to` →
`Số học 3 › Số nguyên tố, ƯCLN và BCNN 0`; the row took a destructive border, read **`0 câu`** in red and said
*"Chuyên đề “Số nguyên tố, ƯCLN và BCNN” chưa có câu hỏi nào dùng được — chọn chuyên đề khác trước khi tạo đề."*
"Tạo đề theo ma trận" stays enabled: the facet count is subject-wide, the row also filters by type and difficulty,
and the server is the authority on what a row can draw from.

**The refusal.** Generating anyway was refused by `POST /exams/{id}/blueprint` (422 `empty_topic`) and the matrix
showed the server's own sentence, under the buttons, in the destructive alert:

> Dòng 2: chuyên đề “Số nguyên tố, ƯCLN và BCNN” không có câu hỏi nào dùng được (0 câu). Chọn chuyên đề khác hoặc
> bổ sung câu hỏi cho chuyên đề này.

Nothing was added (the exam stayed at 2 câu), the refusal is attached to the row it names (`details.fields.row`)
and disappears as soon as the matrix is edited. It does **not** go to the page's error line any more — a refusal
about a row belongs on the row.

**Shortfalls still report.** The first row asked for 3 câu of `Nguyên hàm` where only 2 are `Trắc nghiệm`: the exam
took the 2 it could and the row said **`thiếu 1 câu`**, next to its `3 câu` count. A partly-fillable row is still a
shortfall, not a refusal.

### 2. "Đổi câu": the system picks, or the teacher does (AC-07, ADR-03)

"Đổi câu" now opens a dialog headed by the question it replaces — its stem, and
*"Câu 1 · Trắc nghiệm · 0,5 điểm — câu thay thế giữ nguyên vị trí và số điểm này."* — with both paths in it:

- **"Để hệ thống chọn"** is the automatic replacement the builder has always done (`POST /exams/{id}/questions/{qid}/swap`).
- **the bank below it**: the bank's own search (accent-insensitive, debounced) and its usual filters — môn,
  chuyên đề (the same `TopicPicker`, with the same counts), loại câu, mức độ, tag — defaulted to the exam's
  subject and to the type of the position being replaced. Results are rendered as the bank renders them (stem,
  loại, mức độ, lớp, chuyên đề chính, tags) with a "Chọn" per row, over `POST /questions/search` (limit 20, with
  "195 câu phù hợp — đang xem 20 câu đầu, thu hẹp bộ lọc để thấy câu cần tìm").

**A question already in the exam cannot be chosen twice.** Searching `nguyen ham` while both of the exam's
questions matched, both rows offered a disabled **"Đã có trong đề"**.

**A question of another type is refused, not silently re-priced (decision).** The position's part and its default
points both come from the type, so a different type cannot keep both promises of AC-07. The type filter lists every
type (the others labelled `(khác loại)`) so a teacher can look, and rows of another type carry a disabled
**"Khác loại"** — live, filtering to `Trả lời ngắn` gave three results, all disabled. The dialog says what to do
instead: *"Chỉ chọn được câu cùng loại (Trắc nghiệm): phần của đề và điểm mặc định đều theo loại câu. Muốn dùng câu
khác loại thì bỏ câu này rồi thêm câu đó từ ngân hàng — đề sẽ tự xếp lại phần và điểm."*

**How a chosen swap keeps the place and the points.** `POST /exams/{id}/questions/{qid}/swap` takes no question, and
`apps/api` is not this UoW's to change, so the page hook does it with the endpoints that exist, in the order that
fails safest: add the chosen question → remove the old one → `PUT /order` with the old list, the new id in the old
one's place → `PATCH` the points back when they differ from the type default. If a step fails the question is at
worst at the end of the paper, never gone.

Live, on `Câu 1` deliberately set to **0,5 điểm** (its type default is 0,25):

| Step | Request | Result |
| --- | --- | --- |
| choose `Phương trình 4^{2x-4}=16…` | `POST /exams/{id}/questions` `{question_ids:[d945aa50-…]}` | added at the end |
| | `DELETE /exams/{id}/questions/{old}` | old one gone, positions renumbered |
| | `PUT /exams/{id}/order` | the chosen question back at position 1 |
| | `PATCH /exams/{id}/questions/{new}` `{points: 0.5}` | its points restored |

`GET /exams/{id}` afterwards: `1 · I · mcq · 0.5 · d945aa50-…` and `2 · I · mcq · 0.25 · 55412916-…`, total 0,75 —
same place, same points, the rest of the order untouched. The automatic path on `Câu 2` then replaced it with the
system's pick (`Nguyên hàm của hàm số f(x)=x−sinx`), still at position 2 and 0,25 điểm.

**One fix beyond the ticket's wording.** The per-question points input is uncontrolled (`defaultValue`), and after a
swap React kept the node it had mounted mid-sequence: the box read `0,25` while the exam, the weighting strip and
the server all said `0,5`. It is now keyed by the value (`key={q.points}`), so a change made anywhere remounts it
with what the exam says. Found in the walk, not by the tests.

### 3. What the suite covers

`apps/web/src/__tests__/exam-builder.test.tsx`, +5 cases: the row shows a topic's question count (and the picker's
number is questions, not children); an empty topic is named on its row before generating; the page shows the
server's `empty_topic` refusal, marks the row and drops it when the matrix is edited; the chooser searches the bank
with the position's own filters and refuses a question already in the exam or of another type; a chosen question
takes the place, the number and the points of the one it replaces; the automatic replacement is still one click.

### What this demo changed on live data

- **Created and removed:** one exam, **`8bcd9618-4fde-43c4-9b69-0532cc949205` "Thử ma trận UOW-03"**, built for the
  walk (two matrix rows, two questions, one points edit, two swaps) and deleted afterwards
  (`DELETE /api/exams/{id}` → 204). `POST /exams/search` then listed the same four exams as before, with the three
  document-built papers at 22 questions each.
- **Unchanged:** the three exams built from documents (`b9e582b5-…`, `9eda617d-…`, `f8897dd5-…`) and
  "Kiểm tra 15p - Hàm số bậc 2" (`be4eddb5-…`) were never opened for editing; the refused generation wrote nothing;
  the bank itself was not written to at all — a swap only moves rows of the exam.
