# Product direction — from an exam bank to a growth path per student

Draft for Loc Tran, 2026-09-23. Written after an audit of the code and a survey of how other education
products solve the same problem. Nothing here is committed; it is the recommendation to argue with.

## 1. Where the product actually is

The pipeline (upload → MathType/LaTeX → split → review → bank → exam → assign → auto-grade) is the strong
part and is finished. Everything about a *learner* is one float:

- `student_topic_mastery(student_id, topic_id, mastery, answers, last_at)` — an EMA per leaf topic
  (`ALPHA = 0.3`, difficulty only scales the learning rate), no decay: `last_at` is written and never read.
- Reports are cumulative sums over `answer_facts` inside a filtered window. **No time series anywhere.**
- Practice picks 60% weakest topics / 10% re-ask / rest filler; question choice is `rng.shuffle` over the pool.
- No chart library: progress is drawn with `<div>` width percentages and a colour-coded table.
- Live data: 0 attempts, so every progress screen is empty. The feature has never run on real answers.

Five defects found during the audit, worth fixing before any new feature:

1. An abandoned practice attempt is auto-submitted by the sweep; unanswered questions score 0 and **lower the
   student's mastery** — the improvement metric punishes not practising.
2. "Weak topic" has three different definitions (planner `< 0.8`, `weakest()` with no minimum answer count,
   UI bands at 0.5/0.8). One unlucky answer can define a student's plan.
3. Mastery never decays, so a result from three months ago counts like yesterday's.
4. `rebuild_mastery` is reachable only from bootstrap when the table is empty — tuning the formula cannot be
   applied to existing students.
5. Questions with no topic are silently dropped from mastery, so tagging quality caps the whole feature.

## 2. Principles for this direction

- **Every number must be explainable to a parent in one sentence.** "Đúng 3 câu liên tiếp ở mức vận dụng" beats
  a trained model's 0.63.
- **No flag without an action.** Moodle's analytics API makes this structural: a target declares
  `prediction_actions()`, so an insight always ships with the button that answers it (message, assign practice,
  open detail). Copy the principle.
- **Measure before modelling.** The data that would let us calibrate difficulty is already being thrown away.
  Collect it for a term, then fit anything.
- **Rules beat ML at this size.** Open edX's own "at-risk learner" dashboard is four boolean conditions, not a
  classifier. With 30–300 students per centre, a trained model has neither the data nor the audience.

## 3. Recommended sequence

### F14 — Learning telemetry and item statistics (foundation, no new screens)
- Per answer: `first_seen_at`, `seconds_spent`, `attempt_no`, `is_first_attempt` on `attempt_answers`, carried
  into `answer_facts`. Time on task is the cheapest signal we are not collecting.
- Item statistics per question, computed from facts: **p-value (share correct), first-attempt correct rate,
  discrimination (top vs bottom third), distractor counts**. `key_audit` already computes the ingredients and
  throws them away. First-attempt correct rate is the metric Open edX surfaces to authors, and it is the one
  that exposes an unclear item.
- Weekly snapshot of mastery per (student, topic) so a trend exists at all; plus a bucketed
  `date_trunc('week', …)` variant of the report queries.
- Fix the five defects above: one definition of "weak" (minimum 5 answers), decay in `step()`, abandoned
  practice excluded from mastery, an admin endpoint to recompute, and a "chưa gắn chuyên đề" queue so tagging
  gaps are visible instead of silent.

### F15 — The growth screens (what the customer actually sees)
- **Student**: "Tiến độ của tôi" = mastery map by topic (colour bands + level name), a line of weekly accuracy
  with the class median behind it, the three topics to work on next with a one-click practice button, and the
  streak/effort strip. Open edX's progress page is the template: completion, a grade chart grouped by
  assessment type with a passing line, a weighted summary, and per-question detail split graded vs practice.
- **Teacher**: a students × topics grid with mastery bands, click a band to filter, CSV out — this is Canvas's
  Learning Mastery Gradebook, and it is the single most useful screen we do not have. Plus a "câu khó" tab
  (questions the class got wrong, with the wrong option they chose) as in Kolibri's coach reports, and a
  rule-based "cần chú ý" list (no submission in N days, accuracy falling, mastery below target) where every row
  has the action buttons next to it.
- **Charts**: shadcn charts (Recharts 3) in a thin `"use client"` component, data serialised on the server; each
  chart ships with a text takeaway and a real `<table>` in a `<details>`; ≤4 series, direct labels instead of a
  legend, Okabe-Ito palette, SVG only. Accessibility is not optional for a product used in schools.

### F16 — Mastery gate and review schedule
- **M-of-N mastery** (Kolibri): a topic is mastered when the student answers M of the last N correctly at the
  target difficulty. Explainable, needs no training data, and drives item selection naturally.
- **FSRS** (`py-fsrs`, MIT) at *topic* granularity for scheduling: stability/difficulty/retrievability per
  (student, topic), review due when predicted recall drops below target. Ratings derived from objective signals
  (correct first try → Good, correct after retry → Hard, wrong → Again) — a deviation from FSRS's assumption of
  self-rating, so validate the intervals against real data before trusting them.
- Targets and goals: a per-student target per subject/topic with a due date, so "tiến bộ" has a denominator.
- "Ôn tuần này" replaces the on-demand practice button as the default path.

### F17 — LLM-drafted items with a teacher gate
Order matters: this comes *after* item statistics exist, because that is what makes review defensible.
- Generation is a request for a topic + difficulty + count, producing drafts into the existing review queue —
  never straight into the bank.
- Automatic pre-checks before a human sees a draft: exactly one defensible key, distractors that are not
  trivially wrong, no near-duplicate of an existing question (the trigram/kNN path already exists), valid KaTeX,
  curriculum-topic match, and a solution that reaches the key.
- Every generated item carries its provenance (model, prompt version, reviewer, review date), and after it has
  been used, its p-value and discrimination decide whether it stays. The literature is consistent that LLM items
  need expert review — multiple keys and weak distractors are the common failure modes, and most published work
  skips psychometric evaluation entirely.
- Keep a hard rule: an unreviewed generated item never reaches a student.

### F18 — Organisation dashboard
Cohort and class comparison, coverage of the curriculum, ingestion and review throughput, exports for parents
(CSV/PDF), and a per-class "growth" figure the centre can actually put in a report. Postgres + materialised
views; no separate analytics stack at this size.

## 4. Standards: what to adopt, what to ignore

| Standard | Verdict |
| --- | --- |
| **CASE vocabulary** (CFDocument / CFItem / CFAssociation) | **Borrow the model**, not the software: it gives stable ids for curriculum items and `isRelatedTo` / `exactMatchOf` associations, which is what lets 2018-programme topics map to older papers. Our ltree tree has no way to express that today. |
| **QTI 3.0** | Only at an import/export boundary, and only if a partner asks. Our items are MC / true-false / short answer with LaTeX; a bespoke JSON schema is easier to generate and review against. |
| **LTI 1.3 / OneRoster** | Only when selling into a school that runs an LMS. Not before. |
| **xAPI / Caliper** | Not now. The event log we need is three columns on our own tables. Revisit if a customer demands an LRS. |
| **WCAG 2.2 AA** | Adopt as a working rule now — it is cheap while the screens are being built and expensive to retrofit. Charts need text alternatives, non-colour encoding and 3:1 contrast on the marks themselves. |

## 5. Learner model: what is realistic with our data

- **Elo-style rating** for item difficulty and student ability is the right first model: it updates online after
  each answer, costs nothing to compute, and can be explained. Use it to calibrate `difficulty`, which is a
  hand-typed label today.
- **IRT** needs roughly 200–250 responses per item before estimates are stable — that is a term or two of real
  use for a popular item, and never for a rare one. Plan for it as a later refinement on the top items only.
- **BKT / deep knowledge tracing**: skip. The data volume is not there, and neither is the audience for an
  unexplainable number.
- Guessing on 4-option MCQ means a raw correct/incorrect signal is noisy; prefer first-attempt correctness and
  require several observations before a topic is called mastered.

## 6. Legal and duty-of-care (Vietnam)

- Law 91/2025/QH15 on personal data protection took effect 2026-01-01 and Decree 356/2025 replaced Decree
  13/2023. For children aged 7 and up, processing requires the consent of **both the child and the legal
  representative** — which means a parent/guardian role, a recorded consent trail, and a way to export or delete
  a student's data are product features, not paperwork.
- These are secondary sources; before selling beyond a friendly centre, get a Vietnamese lawyer to review the
  consent flow and retention policy.
- A parent-facing view is a market feature anyway: tutoring centres report to parents, and today that is done by
  hand.

## 7. What to do first

1. F14 telemetry + item statistics + the five fixes (nothing user-visible, but everything later depends on it).
2. Get one real class through a full assignment cycle so `answer_facts` has data; the progress features cannot be
   judged on an empty database.
3. F15 screens, starting with the teacher grid — it sells the product; the student view keeps it.

## 8. Deliberately not doing

A separate analytics stack (ClickHouse/Superset/dbt-style), a trained at-risk model, QTI as the internal item
format, per-student "learning plan" objects, and an opaque default mastery calculation. Each is a well-known
solution to a problem we do not have at this size.

## Sources

Open edX progress page and Aspects dashboards; Moodle analytics API (target/indicator/time-splitting,
`prediction_actions`), competencies and the user report; Canvas Learning Mastery Gradebook and outcome
calculation methods; Kolibri M-of-N mastery and coach reports; ILIAS question pools, post-correction and item
analysis; FSRS (`py-fsrs`, MIT); 1EdTech QTI/LTI/OneRoster/CASE; Elo-vs-IRT literature on sparse data;
2025 work on LLM item generation with human review; WCAG 2.2 and the UK Analysis Function chart checklist;
Vietnam Law 91/2025 and Decree 356/2025. Full URLs are in the research notes attached to this session.
