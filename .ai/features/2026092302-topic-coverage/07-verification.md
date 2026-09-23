---
feature: 2026092302-topic-coverage
environments: [local]
viewports: [desktop, mobile]
---

# Verification — Topic coverage

Signed in as an org admin. The bank holds the 18 official papers; 109 of 377 questions have no
topic, which is what the queue exists to clear.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert |
|---|---|---|---|---|---|
| S1 | The queue lists the untagged questions with the remaining count | `/org/review/untagged` | `settle 2000` | AC-01 | `text=câu chưa gắn chuyên đề`; `no-text=Không tải được` |
| S2 | Filtering by document narrows the queue and keeps the per-document counts | `/org/review/untagged` | `settle 1500; click [aria-label="Đề gốc"]; settle 500; click [role=option] >> nth=1; settle 1500` | AC-01, AC-05 | `text=câu chưa gắn chuyên đề` |
| S3 | A row offers its suggestions with their origin | `/org/review/untagged` | `settle 4000` | AC-02 | `text=Gợi ý` |
| S4 | Selecting rows offers one bulk assignment | `/org/review/untagged` | `settle 1500; click [aria-label="Chọn câu"] >> nth=0; click [aria-label="Chọn câu"] >> nth=1` | AC-03 | `text=Gán chuyên đề` |
| S5 | A model suggestion arrives for a question the rules could not place, marked AI | `/org/review/untagged` | `settle 90000; scroll text=· AI; settle 500` | AC-06 | `text=· AI`; `no-text=Đang hỏi AI` |
| S6 | The bank reports how many questions carry no topic | `/org/bank` | `settle 2000` | AC-05 | `no-text=Không tải được` |

## Not verified here

AC-04 (a question the classifier cannot place waits for review instead of being auto-approved)
happens inside ingestion with no screen of its own: it is covered by `tests/test_topic_suggest.py`
and `tests/test_documents_api.py`, and by the golden re-parse of the 18 papers.

AC-07 (a model that is off, failing or slow degrades to the rule candidates) cannot be produced from the browser
without disabling the organisation's model mid-run, which would change live configuration for the sake of a
screenshot. It is covered by `tests/test_topic_coverage.py` and the handler tests in
`tests/unit/test_ingestion_handlers.py`, which cover the disabled, erroring, timing-out and rambling model.

## Notes

The suggestions a row shows come from two requests: the rules answer in about 0.1 s and the
model takes tens of seconds, so S3 waits before the screenshot. A model that is off or slow is
not a failure here — the rule candidates are what the step asserts.

The `Assert` column names text from the page body, not from the sidebar: at 390 px the sidebar is collapsed, so a
claim on its label passes on desktop and fails on mobile for a reason that has nothing to do with the feature.

A suggestion renders as `<percent>% · <origin>`, so S5 asserts `· AI` rather than `AI`: the bare word also appears
in the sidebar ("Model AI") and in the "Đang hỏi AI…" hint, and an assertion that matches those is green while the
model has produced nothing — the false pass this file exists to avoid. `no-text=Đang hỏi AI` is what makes the
step wait for the model instead of photographing the spinner, and the `scroll` brings the chip into the frame —
an assertion can be satisfied by a row below the fold, which would leave a screenshot that proves nothing.
