# Platform foundation

## Problem
Tutoring centers have no shared place to keep their exam material, and every later Examind
capability (ingestion, review, exams, adaptive practice) needs the same base: a running
self-hosted stack, isolated tenants, accounts that students without email can use, and a
knowledge taxonomy fine-grained enough to report "Giải tích › Nguyên hàm › Từng phần".

## Outcome
---
feature: platform-foundation
slug: 2026092101-platform-foundation
owner: Loc Tran
created: 2026-09-21
status: approved
---

## Success signal
From a clean checkout, `docker compose up` brings the stack up and a center admin can import
30 students from CSV, after which any of them logs in with `org_code + username + password`
and is forced to change the temporary password — all in under 5 minutes.

## Out of scope
- Uploading or parsing exams (feature `exam-ingestion`)
- Question bank CRUD beyond the demo question used by `QuestionView` (feature `question-review`)
- Google OAuth, email-based password reset — students often have no email; post-MVP
- Subdomain-per-center routing — post-MVP
- Deploying to the Oracle VM — documented, executed by Loc Tran (needs an account)

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Platform operator (super_admin) | Nothing to operate | Creates/suspends centers from one screen |
| Center admin (org_admin) | Accounts in spreadsheets | Imports a class of students from CSV, hands out temp passwords |
| Teacher | Topics live in their head | Browses and edits one topic tree + tags shared by the center |
| Student | — | Logs in with center code + username + password |

## Constraints
| Kind | Detail |
| --- | --- |
| Cost | Free/open-source only; everything self-hosted in one Docker Compose |
| Platform | Must build on arm64 (Mac M-series, Oracle Ampere) and amd64 |
| Tenancy | Every tenant row carries `organization_id`; code is the human-facing key |
| Deadline | None stated |

## Existing surface touched
- Reused components: none (greenfield) — see `.ai/architecture.md` target layout
- Adjacent features: all later features depend on users, orgs, topics, tags, `QuestionView`
- Entry points: `/login`, `/admin/orgs`, `/org/users`, `/org/classes`, `/org/topics`, `/org/tags`, `/dev/question-preview`
