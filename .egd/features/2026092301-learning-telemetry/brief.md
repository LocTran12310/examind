# Measure learning, and stop the mastery number lying

## Problem
The product reads exam papers well; what it knows about a *student* is one float per topic. There is no time
axis, no per-question timing, no calibrated difficulty, and four defects make the number itself untrustworthy:
an abandoned practice attempt is auto-submitted and its unanswered questions lower mastery; "weak topic" means
three different things in three files and needs no minimum number of answers; mastery never decays; and the
formula cannot be recomputed after a change. Everything the direction note (`.ai/product-direction.md`) proposes
next — growth screens, a review schedule, LLM drafts reviewed against item quality — needs data this feature
collects and rules it repairs. Nothing user-visible ships here beyond item statistics on a question.

## Outcome
---
feature: learning-telemetry
slug: 2026092301-learning-telemetry
owner: Loc Tran
created: 2026-09-23
status: approved
---

## Success signal
After one real assignment: `answer_facts` carries seconds and attempt number for every answer; a question detail
shows p-value, first-attempt correct rate and distractor counts; an abandoned practice attempt leaves mastery
unchanged; a weekly snapshot exists for every student with answers; `POST /analytics/mastery/rebuild` reproduces
today's numbers from the facts.

## Out of scope
- Growth screens, charts, dashboards (next feature)
- Spaced repetition scheduling, goals, M-of-N mastery gate
- Elo/IRT calibration — this feature only collects what a later one would calibrate from
- LLM item generation

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Student | Practising and abandoning lowers mastery; one unlucky answer defines "weak" | Only answered questions count; a topic is weak after enough evidence |
| Teacher | Difficulty is whatever someone typed; no way to see which question misleads a class | Each question shows how many got it right, how many at first try, how it discriminates, and which wrong option attracts |
| Owner | Changing the mastery formula cannot be applied to existing students | A recompute replays the history |

## Constraints
| Kind | Detail |
| --- | --- |
| Data | No destructive migration; existing facts keep working with the new columns null |
| Privacy | Timing is per answer, not keystroke- or screen-level; no new personal data category |
| Performance | Statistics are read models over `answer_facts`; no new analytics service |
