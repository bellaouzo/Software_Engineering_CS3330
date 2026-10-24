# Project docs

Team documents for the CS 3300 maintenance ticketing project: requirements,
Test Plans, sprint notes, diagrams, and similar. Word docs, PDFs, and
spreadsheets go here.

This folder holds documentation only. Code, templates, and database migrations
live in their own folders (see `AGENTS.md`).

## Markdown vs Word docs

Markdown files (`.md`) are for developers and AI tools: setup guides, checklists,
and notes about how the code works. They live in `guides/` so they diff cleanly
in Git and AI agents can read them. Word docs, PDFs, and spreadsheets are for
the class deliverables and stay out of `guides/`.

- `guides/` - Markdown guides. `AGENTS.md` at the repo root is the overview
  and links to each one:
  - `setup-and-running.md` - running the app, `dev.py`, `.env`, Git/`gh` setup
  - `conventions.md` - routes, templates, Supabase queries, login, fixed values
  - `naming-conventions.md` - names for files, functions, URLs, CSS, tables
  - `database-schema.md` - tables, triggers, RLS, known issue, migrations
  - `file-size-and-splitting.md` - line limits per file type and how to split
  - `git-workflow.md` - branches, PRs, and the merge steps
  - `testing.md` - cross-functional testing and Test Plans
  - `auth-helpers-examples.md` - how routes use the login and database helpers
  - `supabase-live-auth-setup.md` - live Supabase steps for login

## Suggested layout

Add subfolders as needed for the Word docs, PDFs, and spreadsheets, for example:

- `requirements/` - requirements spreadsheet and related specs
- `test-plans/` - one numbered Test Plan per file
- `design/` - diagrams, mockups, wireframes
- `meetings/` - agendas and notes

## Naming files

- Use lowercase with hyphens and no spaces: `test-plan-01-ticket-submit.docx`.
- Number files that have an order (Test Plans, sprint reports).
- Keep one topic per file. Edit the existing file rather than saving copies like
  `final-v2`; Git keeps the history.
