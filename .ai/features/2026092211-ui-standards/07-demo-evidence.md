# Demo evidence — ui-standards (2026-09-22)

- Duplicates: cause found in the dev data — the 18 documents of 08:45 were copies uploaded by `golden_live.py`,
  which appended bytes to force a new parse; Loc Tran's real upload at 10:47 therefore had other hashes. Now: browser
  SHA-256 + `/documents/check`; per-file choice; the same content is never stored twice; the golden runner re-parses
  with `on_duplicate=replace`. Tests `test_document_duplicates.py` (3), `documents.test.tsx`.
- Operators: `test_filter_operators.py` (text * = + - !, compare, 422, day bounds), `data-table.test.tsx`.
- Time zone: `lib/datetime.test.ts` passes under `TZ=America/New_York`; server `business_date` / `day_start`.
- Exam order: draft mode, one PUT (`exam-builder.test.tsx`).
- Preview dialog maximised (live, JS): body 708 px of a 752 px dialog, scrolls 3 304 px, no inner max-height.
- shadcn: no raw button/input/select/textarea/label/table/details/kbd left outside components/ui (only `<a>` under
  `Button asChild`); KaTeX SVGs inside option buttons keep their size (20×15.9 px measured live).
- API 305 passed (+1 skipped: official set needs EXAMIN_DIR), web 142, tsc/eslint/next build clean.
