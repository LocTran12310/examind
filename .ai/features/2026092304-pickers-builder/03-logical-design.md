---
feature: pickers-builder
adr_count: 3
---

# Logical design

## Approach
- **Counts (ADR-01)**: `POST /questions/facets` already answers question counts per topic, subtree-summed. The
  pickers take those counts as a prop instead of showing `children.length`; the page hooks fetch the facets for
  the subject in hand. One source of truth for "how many questions are there", the same one the bank filters use.
- **Suggestion as the picker's starting point**: `TopicPicker` gains `initial` (a topic id): it expands its
  ancestors, focuses it and leaves the confirmation to the teacher (A-01). The review queue and the tagging queue
  pass the row's best suggestion.
- **Bulk by suggestion (ADR-02)**: a new `POST /questions/bulk/topics` taking pairs `{question_id, topic_id}`
  (≤200) so a page's worth of different topics is one request; it answers `{updated, skipped}`. The queue sends
  each selected row's top suggestion and reports what had none.
- **Bank classification**: `POST /questions/bulk` `set` gains `subject_id` and `grade`, validated like the single
  update; the bank toolbar gains the two actions.
- **Builder**: the blueprint row keeps its fields on one line at desktop width and stacks deliberately below it;
  generation refuses a row whose pool is empty, naming the topic (AC-06); "Đổi câu" opens a chooser with the
  bank's own filters, next to the automatic replacement.
- **Long filters (A-07)**: the option list scrolls inside the dropdown and asks for the next page as it reaches
  the end, reusing the resource's search hook.

## Alternatives rejected
| Option | Why not |
| --- | --- |
| Compute topic counts in the picker from the bank list | The list is paged; the picker would count a page, not the bank |
| Apply the top suggestion automatically for a whole page | The measurement says the model is wrong often enough (topic-coverage); a click per page is the honest middle |
| One request per question for bulk tagging | 20 requests for one click, and a half-applied page when one fails |
| A separate "swap" screen | The builder already has the filters; a dialog keeps the exam on screen |

## Domain model
No schema change. `question_topics.source` stays `manual` for a teacher's decision, including one taken from a
suggestion — a human confirmed it.

## Contracts
| Method & path | Notes |
| --- | --- |
| `POST /questions/bulk/topics` | `{pairs: [{question_id, topic_id}]}` (≤200) → `{updated, skipped}` |
| `POST /questions/bulk` | `set` gains `subject_id`, `grade` |
| `POST /questions/facets` | unchanged; now also drives the pickers' counts |
| `POST /exams/{id}/blueprint` | refuses a row with an empty pool: 422 `empty_topic` naming the topic |

## State ownership
| State | Owner | Lifetime |
| --- | --- | --- |
| Picker expansion and focus | the dialog | while open |
| Facet counts | React Query, per subject | until invalidated by a tagging change |

## Error taxonomy
| Condition | Code | HTTP |
| --- | --- | --- |
| More than 200 pairs | `validation_error` | 422 |
| A pair whose topic is not of the question's subject | `validation_error` | 422 |
| Blueprint row with an empty pool | `empty_topic` | 422 |

## Observability
Bulk tagging is audited as the existing bulk edit, with the number of pairs.

## ADRs

### ADR-01 — The number beside a topic is questions, from the facets
**Context:** It is the count of child topics today, and a teacher reads it as questions — so empty topics get
chosen and the builder quietly returns fewer questions.
**Decision:** Pickers take counts from `POST /questions/facets` (subtree totals, subject-scoped, usable only).
**Consequences:** One number, one meaning, already tested; the picker needs the subject in hand.
**Status:** accepted

### ADR-02 — One request applies many different topics
**Context:** Suggestions are per question, so clearing a page means twenty different topics.
**Decision:** `POST /questions/bulk/topics` takes pairs and answers what it skipped.
**Consequences:** A page is one click and one transaction; the queue can report "3 câu chưa có gợi ý".
**Status:** accepted

### ADR-03 — A swap is the teacher's choice, with an automatic option
**Context:** Today the system picks; a teacher who knows the paper cannot say which question to use.
**Decision:** Keep the automatic replacement and add a chooser with the bank's filters.
**Consequences:** The builder stays usable for a quick pass and precise for a careful one.
**Status:** accepted
