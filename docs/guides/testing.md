# Testing

Summary in `AGENTS.md` > Working on a change.

- **Cross-functional rule:** whoever wrote the Back End for a feature does not
  test its Front End, and vice versa — Front End writers test Back End work and
  Back End writers test Front End work. Your testing pair is also who reviews
  your PR (see `git-workflow.md`).
- Test methods map to the requirements spreadsheet's T/A/I/O column: Test,
  Analysis, Inspection, Observation.
- Each test should be documented as its own numbered Test Plan, per the class
  Test Plan template — don't lump multiple tests into one plan. Test Plans are
  Word docs and go in `docs/` (e.g. `docs/test-plans/`), not in `docs/guides/`.
- The known RLS issue (requesters can update their own ticket's status; see
  `database-schema.md`) should become one of these test cases once the team
  reaches testing.
