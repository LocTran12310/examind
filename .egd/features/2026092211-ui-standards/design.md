---
feature: ui-standards
adr_count: 3
---

# Logical design

## Approach
- **Duplicates**: `POST /documents/check {files:[{name,sha256}]}` → same_file / same_name (NFC, case-insensitive);
  `POST /documents` gains `on_duplicate` (skip | replace | keep_both) + `replace_id`; replace re-parses (same content) or
  swaps the stored file of the chosen document (approved and exam questions kept). Upload form hashes files in the browser
  (Web Crypto) and asks per file. `golden_live.py` re-parses instead of uploading modified copies.
- **Operators**: `services/paging.py` reads `<col>_op` (TEXT_OPS, COMPARE_OPS), kinds text/number/date/day; `FilterCell`
  shows a symbol button (InputGroup + DropdownMenu radio "Chọn kiểu lọc").
- **Time zone**: `app/core/timezone.py` (`business_date`, `day_start`, `day_end_exclusive`, setting `business_tz`);
  web `lib/datetime.ts` (`formatDateTime`, `formatDate`, `toBusinessInput`, `fromBusinessInput` with +07:00).
- **Order**: `ExamQuestions` draft mode (swap / drag / ↑↓ within a section) → one `PUT /exams/{id}/order`.
- **shadcn**: raw tags replaced (Label, Button, Checkbox, Kbd, Collapsible, Table, Input); preview dialog body scrolls in FormDialog.

## Alternatives considered
| Option | Why not |
| --- | --- |
| POST-body filters | Examind keeps list state in the URL (F6) |
| Browser-local display | Reports and schedules must read the same everywhere |

## Domain model
No schema change.

## Contracts
| Method & path | Role | Notes |
| --- | --- | --- |
| `POST /documents/check` | staff | duplicates per file |
| `POST /documents` `on_duplicate`, `replace_id` | staff | action created/skipped/reparsed/replaced |
| list endpoints `<col>_op` | as before | 422 bad_filter |

## State ownership
| State | Owner | Lifetime |
| --- | --- | --- |
| Order draft | ExamQuestions state | until saved |

## Failure modes
| Condition | Code | HTTP | UI |
| --- | --- | --- | --- |
| Unknown operator | `bad_filter` | 422 | toast |
| Bad on_duplicate | `validation_error` | 422 | row error |

## Observability
Audit `document.replace`.

## ADRs

### ADR-01 — Filter operators in URL params
**Context:** One operator convention for every list.
**Decision:** Fixed symbols/labels, serialized as `<col>_op`.
**Consequences:** Links keep filters; server whitelist.
**Status:** accepted

### ADR-02 — Business time zone Asia/Ho_Chi_Minh
**Context:** UTC storage, Vietnamese days.
**Decision:** Fixed zone for display and day bounds; explicit offsets on input.
**Consequences:** Same results for every browser and server zone.
**Status:** accepted

### ADR-03 — Content hash + name for duplicates
**Context:** Re-uploads created copies.
**Decision:** Hash decides "same file", name decides "new version"; the user chooses per file.
**Consequences:** No silent duplicates; replace keeps curated questions.
**Status:** accepted
