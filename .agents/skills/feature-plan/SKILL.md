---
name: feature-plan
description: Start or continue a planned feature through the AI-DLC controller — gates, assumptions, ADRs, units of work, tickets and evidence.
---

# Plan a feature

Feature work lives on disk in `.ai/features/YYYYMMDDNN-<slug>/` and is gated by `scripts/aidlc`.
Read the previous feature (`.ai/features/2026092212-architecture-refactor/`) as the shape to copy.

## Flow

```bash
./scripts/aidlc init <slug> --profile none          # scaffolds the folder and state
./scripts/aidlc -d .ai/features/<dir> status        # always start here; never infer the gate
```

| Gate | You write | Then |
| --- | --- | --- |
| G0 | `00-intent.md` (problem, personas, success signal, out of scope, constraints) | `pass G0` |
| G1 | `01-assumptions.md` (each row: confidence, blocking, blast radius, resolution), `02-requirements.md` (US + AC in gherkin) | `pass G1` |
| G2 | `03-logical-design.md` (approach, rejected alternatives, contracts, error taxonomy, ADRs) | `pass G2` |
| G3 | `plan_spec.py` → `python3 scripts/gen_plan.py <dir> <dir>/plan_spec.py` → `uow_graph.py <dir> --write` | `pass G3` |
| G4 | the code, ticket by ticket | `scripts/close_ticket.sh <dir> T-xx-yy` |
| G5 | `07-demo-evidence.md`, a section in `.ai/final-review.md` | `pass G5` |

- Units of work are vertical slices that can be demoed on their own; tickets are ≤ 4h with a done-when list.
- `close_ticket.sh` runs the ticket's tests through `scripts/verify.sh` and records the run — it must exit 0.
- Never hand-edit `.aidlc-state.yaml`. When reality contradicts the plan, `aidlc reopen <gate> --reason …`
  and fix the artifact before the code.
- Assumptions that the owner accepted in chat are recorded as "Accepted under blanket pre-approval …" and listed
  again in the final review, so one review covers them all.
