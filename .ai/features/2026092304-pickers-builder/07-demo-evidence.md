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
