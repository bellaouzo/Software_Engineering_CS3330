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
- TP-010, TP-012, and TP-013 run against the demo data from
  `seed_demo_data.py`, so everyone tests with the same accounts and tickets
  (see `demo-data.md`). Note the `--tickets` count used in the Test Plan.
- The staff-only ticket update policy (F-001; see `database-schema.md`) is
  verified by TP-004 (traces 6, 7) and TP-008.
