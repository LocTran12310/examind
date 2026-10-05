---
feature: subject-scoped-bank
adr_count: 3
---

# Logical design — Question bank filtered by subject first

## Approach
**Data.** Migration 0016: `tags.subject_id` (nullable FK, index) + backfill (a non-source tag whose
tagged questions all have one subject gets it). `Tag` model gains the column.

**API.**
- `bank.filtered` gains `subject_id="none"` (questions without subject) and `school_year` (exists on
  `source_documents.meta->>'school_year'`).
- `GET /questions/facets` takes the list filters and returns
  `{subjects:[{id|null,count}], topics:[{id,count}], types, difficulties, grades, periods, school_years, tags}`;
  each facet is counted with every filter except its own dimension; topic counts join
  `question_topics → topics x` with `x.path <@ t.path` over the subject's topics (subtree totals).
- `/tags?subject_id=` returns that subject's tags plus shared ones; `TagIn/TagUpdate/TagOut` carry
  `subject_id`; uniqueness stays (org, group, name).

**Web.**
- `components/bank/SubjectTabs.tsx` (shadcn Tabs): subjects + counts; writes `subject_id` to the URL,
  removes `topic_ids`, `topic_id`, `tag_ids`; remembers the choice in localStorage per org.
- `components/bank/FilterSheet.tsx` (shadcn Sheet): draft state from URL; sections (Collapsible):
  Chuyên đề (`TopicTreeSelect` with counts), Loại câu, Mức độ, Lớp, Đợt kiểm tra, Năm học,
  Nguồn đề (source tags), Tags (by group), Trạng thái; footer "Xóa lọc" / "Áp dụng".
- `components/bank/FilterChips.tsx`: one chip per active filter (topic path, tag, …), × removes it.
- `BankFilters` becomes: search + "Bộ lọc (n)" + chips. Bank page fetches `/topics?subject_id` and
  `/tags?subject_id` for the chosen subject and `/questions/facets` with the current query.
- Exam page: topics and tags for the exam's subject passed to `BlueprintEditor`.
- Tags page: subject column/filter, subject select in the tag form.

## Alternatives considered
| Option | Why not |
| --- | --- |
| Keep a "Môn" dropdown among the other filters | Topics/tags of all subjects stay mixed; the root of the complaint |
| Client-side counts | Only the current page is loaded; counts must be server-side |
| `users.last_subject_id` | A per-org browser preference like the year selector is enough and needs no API |

## Domain model
| Entity | Change | Notes |
| --- | --- | --- |
| `Tag` | + `subject_id` nullable | null = shared |

## Contracts
| Method & path | Role | Notes |
| --- | --- | --- |
| `GET /questions?…&subject_id=<id|none>&school_year=` | staff | Page |
| `GET /questions/facets?…` | staff | counts |
| `GET /tags?subject_id=` · `POST/PATCH /tags` `{subject_id}` | staff | shared included |

## State ownership
| State | Owner | Lifetime |
| --- | --- | --- |
| Filters | URL search params | link |
| Last subject | localStorage per org | browser |

## Failure modes
| Condition | Code | HTTP | UI |
| --- | --- | --- | --- |
| Tag subject of another org | `validation_error` | 422 | field |
| Unknown topic in filter | `validation_error` | 422 | toast |

## Observability
None new.

## ADRs

### ADR-01 — Subject as the bank's context
**Context:** Topics and tags only make sense inside one subject.
**Decision:** Tabs choose the subject; subject-specific filters are dropped on switch.
**Consequences:** No mixed-subject view; "Chưa phân môn" tab catches untagged questions.
**Status:** accepted

### ADR-02 — Facets exclude their own dimension
**Context:** Counts must help choose, not collapse to the current choice.
**Decision:** Each facet query applies every filter but its own; topics counted per subtree.
**Consequences:** One query per facet (8 small grouped queries), fine at bank sizes.
**Status:** accepted

### ADR-03 — Optional subject on tags
**Context:** Some tags belong to a subject, others (nguồn đề) to all.
**Decision:** Nullable `tags.subject_id`; lists return subject + shared.
**Consequences:** Existing tags keep working; backfill scopes the obvious ones.
**Status:** accepted
