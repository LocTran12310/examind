@AGENTS.md

## Claude Code specifics

- **Skills**: `.claude/skills/` mirrors `.agents/skills/` — load `api-endpoint`, `api-search`, `web-screen`,
  `db-change`, `ingestion-change` or `feature-plan` before starting that kind of work.
- **Rules**: `.claude/rules/*.md` load when you open the files they scope (API modules, web screens, tests,
  migrations). They repeat the binding parts of this agreement at the place they apply.
- **Evidence**: close planned tickets with `scripts/close_ticket.sh`, which runs `scripts/verify.sh` and records
  the run. Do not tick a done-when box you have not verified.
- **Subagents**: give each one the architecture map, the finished module to copy, and the exact checks to run.
  The API test database is shared, so never run two API suites at once.
