---
feature: topic-coverage
adr_count: 4
---

# Logical design

## Approach
Two slices. The API gains a way to list untagged questions, a suggestion endpoint that reuses the ingestion
rules, and the ingestion rule that an unclassified question waits for review. The web gains one screen that
turns the backlog into a few minutes of clicking.

- **bank**: `has_topic` becomes a filter of `POST /questions/search` (param, `false` = no topic row) so the queue
  is an ordinary list with the usual paging and column filters. `POST /questions/suggest-topics {question_ids}`
  answers `{suggestions: {question_id: [{topic_id, name, path, score, source}]}}`, at most three per question.
  Assignment reuses `POST /questions/bulk` with `set.primary_topic_id`, which already exists.
- **ingestion** owns the classifier and exposes `suggest_for(org_id, subject_id, texts)` from
  `application/api.py`; bank reaches it through a port implemented by an adapter wired in `main.py`, the same way
  bank already reaches taxonomy. Suggestions are computed on demand, nothing is stored.
- **ingestion** also changes what it stores: when the suggester produced no topic for a question, the question is
  `needs_review` with a warning "chưa gắn chuyên đề" in the document log, whatever its parse confidence.
- **web**: `Duyệt câu hỏi › Chưa gắn chuyên đề` — a DataTable of untagged questions (stem preview rendered with
  the existing question renderer, subject, document, created date), a suggestion row per question with the three
  candidates as buttons, a TopicPicker for anything else, multi-select with "Gán chuyên đề cho N câu", and the
  remaining counter. Keyboard: 1/2/3 pick a suggestion, ↑↓ move, so a teacher can work through a paper quickly.

## Alternatives rejected
| Option | Why not |
| --- | --- |
| Store suggestions in `question_topics` with `source='knn'` and a low score | A stored guess looks like a decision; the queue would need to distinguish them everywhere |
| Re-run the whole ingestion pipeline on the 18 papers | Re-parses everything to change one field, and would fight the "keep approved questions" rule |
| A new classifier (embeddings/pgvector) | The existing rules are good enough to rank three candidates; a better classifier is its own feature |
| Auto-assign the top suggestion above a threshold | That is what already failed silently; a human confirms, and the acceptance rate tells us whether to automate later |

## Domain model
No schema change. `question_topics` keeps `source` (`manual` when a teacher picks from the queue).

## Contracts
| Method & path | Notes |
| --- | --- |
| `POST /questions/search` | `has_topic: bool` at the top of the body |
| `POST /questions/suggest-topics` | `{question_ids: [uuid], use_model?: bool = true}` (≤50) → `{suggestions: {id: [{topic_id, name, path, score, source}]}, model_used: bool}`; `source` is `keyword | similar | ai` |
| `POST /questions/bulk` | unchanged, used with `set.primary_topic_id` |
| `POST /questions/facets` | already reports `topics["none"]`; gains the same count per document |

## State ownership
| State | Owner | Lifetime |
| --- | --- | --- |
| Suggestions | computed per request | the request |
| Chosen topic | `question_topics` | until changed |

## Error taxonomy
| Condition | Code | HTTP |
| --- | --- | --- |
| More than 50 ids in one suggestion request | `validation_error` | 422 |
| A question of another organisation | `not_found` | 404 |
| Topic from another subject than the question | `validation_error` | 422 |

## Observability
The ingest log gains the count of questions left untagged; the queue's bulk apply is audited like other bulk edits.

## ADRs

### ADR-01 — Suggestions are computed, never stored
**Context:** A guess written into `question_topics` is indistinguishable from a teacher's decision.
**Decision:** `POST /questions/suggest-topics` runs the existing rules on demand and returns candidates with score
and origin; only a human decision is written, with `source='manual'`.
**Consequences:** No migration, no stale suggestions; a few hundred ms per batch of questions.
**Status:** accepted

### ADR-02 — An unclassified question waits for review
**Context:** 101 untagged questions were auto-approved and therefore invisible.
**Decision:** Ingestion stores a question with no topic as `needs_review`, with the reason in the document log.
**Consequences:** Uploads of papers the classifier handles poorly produce more review work — which is the point;
the tagging queue is where that work is done.
**Status:** accepted

### ADR-03 — The bank reaches the classifier through ingestion's application API
**Context:** The rules (cues, kNN) live in the ingestion module; the queue lives in the bank.
**Decision:** `ingestion.application.api.suggest_for(...)` is the only entry point; bank defines a port and an
adapter wired at the composition root, as it already does for taxonomy and identity.
**Consequences:** The dependency rules stay green; the classifier keeps one home.
**Status:** accepted

### ADR-04 — The model suggests where the rules are silent
**Context:** On the real backlog the rules produced candidates for 14 of 102 questions — those questions are by
definition the ones the cues failed on, so A-05 ("no model in the queue") was refuted by measurement.
**Decision:** `suggest_for` keeps the rule candidates first and, for questions with none or with a best score
below `WEAK_KEYWORD`, asks the organisation's enabled tagging model in batches (the ingestion stage's prompt and
`_resolve` are reused, not re-written). Model candidates carry `source: "ai"`, are constrained to the subject's
topic tree, and never outrank a strong keyword candidate. A disabled, missing, failing or slow model degrades to
the rule candidates and sets `model_used: false`.
**Consequences:** The queue becomes usable for the 88 questions the rules cannot place; latency is a batched model
call per page; the acceptance rate of `ai` candidates is what tells us whether to automate any of it later.
**Status:** accepted
