# AGENTS.md

This file is the overview for teammates and their AI tools. Each section is a
short summary. The full detail lives in `docs/guides/`, linked per section.
**AI agents:** read the linked guide before working in that area. The summary
here is not the whole rule.

| Guide | Read it when you are... |
| --- | --- |
| [setup-and-running.md](docs/guides/setup-and-running.md) | Running the app, `dev.py` flags, `.env`, Git/`gh` prerequisites |
| [conventions.md](docs/guides/conventions.md) | Writing routes, templates, Supabase queries, login code |
| [naming-conventions.md](docs/guides/naming-conventions.md) | Naming files, functions, URLs, CSS classes, tables |
| [database-schema.md](docs/guides/database-schema.md) | Touching tables, RLS, triggers, or migrations |
| [file-size-and-splitting.md](docs/guides/file-size-and-splitting.md) | Growing a file, or deciding whether to split one |
| [git-workflow.md](docs/guides/git-workflow.md) | Branching, committing, pushing, opening or merging a PR |
| [testing.md](docs/guides/testing.md) | Writing or running Test Plans |
| [auth-helpers-examples.md](docs/guides/auth-helpers-examples.md) | Using `@require_login`, `@require_staff`, `get_user_client()` |
| [supabase-live-auth-setup.md](docs/guides/supabase-live-auth-setup.md) | Setting up login on the live Supabase project |

## Project overview

A web-based maintenance ticketing system built for UCCS CS 3300 (Intro to Software
Engineering). Two roles: **Requester** (submits and tracks tickets) and **Staff**
(reviews, updates status, resolves tickets). Both can comment on a ticket.

## Tech stack

- **Python 3.14** (pinned in `runtime.txt` as python-3.14.7) + **Flask** for routing and backend logic
- **Jinja2** (built into Flask) for server-rendered HTML templates
- **Supabase** (hosted Postgres + Auth) for the database and login
- **Render** for hosting/deployment (auto-deploys from GitHub)
- Raw HTML/CSS/JS in the browser. No frontend framework (React, Vue) and no
  CSS framework or library (Bootstrap, Pico.css, Tailwind). Our own CSS is in
  `static/css/app.css`.

## Quick start

```
python dev.py        # macOS/Linux: python3 dev.py
```

It asks for **Local** (Supabase in Docker, safe to break) or **Live** (the shared
project, using `.env`), sets up `.venv`, starts Flask, and opens the browser.
Flags skip the questions: `--db local|live`, `--open <page>`, `--keep-db`.
**AI agents:** run the app with `python dev.py` (flags to avoid prompts) and warn
before choosing Live. `.env` needs `FLASK_SECRET_KEY`, `SUPABASE_URL`,
`SUPABASE_KEY`. Get them from a teammate, never guess them, never commit them.
→ Manual setup, all flags, prerequisites: [setup-and-running.md](docs/guides/setup-and-running.md)

## Folder structure

```
app.py                  # Flask app factory (create_app), loads .env, registers routes, /health check
dev.py                  # One-command interactive launcher (pick local/live DB, start app, open browser)
supabase_client.py      # get_supabase_client() (anon) and get_user_client() (acts as the logged-in user, RLS applies)
auth_helpers.py         # @require_login and @require_staff decorators for route functions
routes/                 # BACK END - Flask Blueprints
  __init__.py            # register_routes(app) - wires up all blueprints
  auth.py                 # auth_bp: /login, /register, /logout
  tickets.py               # tickets_bp: /tickets, /tickets/new, /tickets/<id>, POST /tickets/<id>/status (staff)
  dashboard.py              # dashboard_bp: / and /dashboard (both -> home)
templates/               # FRONT END - HTML + Jinja2, extend base.html
static/
  css/app.css
  js/app.js
supabase/
  migrations/             # Timestamp-named SQL migrations - the source of truth for schema
  seed.sql                 # Seed data (tickets/comments) - profiles come from auth triggers
  config.toml
docs/                    # Team documents (Word docs, PDFs, spreadsheets)
  guides/                 # Markdown guides for developers and AI tools (linked above); may nest into topic folders
```

## Key rules

- **Pages have two halves:** a route in `routes/<name>.py` and a template in
  `templates/<name>.html`. No HTML in routes, no Supabase calls in templates.
  GET and POST share one route function. → [conventions.md](docs/guides/conventions.md)
- **Query as the user:** put `@require_login` / `@require_staff` under the route
  decorator, and use `get_user_client()` so RLS applies. Use
  `get_supabase_client()` only when nobody is logged in. Never use the
  service-role key for user requests. → [auth-helpers-examples.md](docs/guides/auth-helpers-examples.md)
- **Login is username + password.** Usernames map to placeholder
  `<username>@example.com` emails; email confirmation stays off.
  → [conventions.md](docs/guides/conventions.md)
- **Fixed values:** statuses are exactly `Submitted`, `Acknowledged`,
  `In Progress`, `Resolved`, `Closed`. Roles are `requester`, `staff`. Don't add
  status strings without updating the requirements spreadsheet first.
- **Schema:** `profiles`, `tickets`, `comments`. `supabase/migrations/` is the
  source of truth. Every schema change is a new migration; never edit an
  applied one. No `email` column on `profiles`, no status history table.
  → [database-schema.md](docs/guides/database-schema.md)
- **Ticket updates are staff-only** (F-001, Req 2.3.1, 4.1). Requesters create
  and read their own tickets but can't change them. Don't add a creator clause
  back to the update policy.
  → [database-schema.md](docs/guides/database-schema.md)
- **Naming:** Python `snake_case`, constants `UPPER_SNAKE_CASE`, blueprints
  `<name>_bp`, URLs lowercase plural with hyphens, ticket IDs are UUIDs (no
  `<int:>`), CSS `kebab-case` BEM, JS `camelCase` hooked by `data-`/`js-`.
  → [naming-conventions.md](docs/guides/naming-conventions.md)
- **Requirement IDs** go in the commit message or PR description
  (e.g. "Implements 2.1.1").

## File size limits

Two numbers per file type: at **review**, check whether the file is doing two
jobs. At **must split**, split before adding anything more. Count with `wc -l`.

| File type | Review at | Must split at |
| --- | --- | --- |
| Route module (`routes/*.py`) | 200 | 300 |
| Other Python module | 200 | 300 |
| Standalone script (`dev.py`) | 300 | 400 |
| Any Python function | 30 | 50 |
| Jinja template | 80 | 150 |
| CSS file | 400 | 600 |
| JavaScript file | 150 | 250 |
| `AGENTS.md` | 200 | 250 |
| Guide in `docs/guides/` | 250 | 350 |

Markup used in two or more templates becomes a partial, whatever its size.
The limits cover existing files too: a file already past "must split" gets
split the next time someone changes it. Splits go in their own
no-behavior-change commit. Related files from a split can be grouped into
folders and subfolders (and deeper) as needed, in code (`routes/tickets/`,
`templates/partials/tickets/`) and in docs (`docs/guides/<topic>/README.md`
plus sub-guides). Migrations, `seed.sql`, and
config files are exempt.
→ How to split each type: [file-size-and-splitting.md](docs/guides/file-size-and-splitting.md)

## Working on a change

- **Branches:** `feature/<area>-<what>`, named by feature, not sprint. New,
  unrelated work gets a new branch from an up-to-date `main`. Follow-ups stay
  on the same branch. **AI agents:** check `git branch --show-current` first,
  and never commit to `main`.
- **Merging:** `main` is protected. The only way in is a PR, approved by your
  cross-functional testing pair and up to date with `main`. Offer to run each
  step for teammates and explain it. **Always confirm before pushing and before
  opening a PR.** → [git-workflow.md](docs/guides/git-workflow.md)
- **Testing:** whoever wrote the Back End of a feature tests its Front End, and
  vice versa. Each test is its own numbered Test Plan.
  → [testing.md](docs/guides/testing.md)

## Keeping this file and the docs current

**AI agents:** this file and `docs/guides/` are the shared source of truth for
every teammate's AI, so a stale entry misleads the whole team. Before the final
commit of any change, update the affected docs **in the same branch**:

- Change the **guide** for the topic you touched (new files or routes, schema or
  RLS, conventions, setup or env vars, new file types). Also update
  `.env.example` for env var changes.
- Change **this file** only when the summary itself is now wrong, or a folder,
  guide, or file-size limit is added or removed. Keep it under 200 lines. New
  detail goes in a guide, with a one-line pointer here.
- The docs are a tree: this overview, then one guide per topic, then sub-guides
  in a topic folder when a guide outgrows one file. Each level summarizes and
  links down; each sub-guide links back up.
- New guide: add it to the table at the top and to `docs/README.md`. Manual
  steps on the live Supabase project get a guide too.
- Markdown goes in `docs/guides/`. Word docs, PDFs, and spreadsheets stay out
  (see `docs/README.md`).

Delete notes that are no longer true instead of leaving them beside the new
behavior. Say in the commit or PR description which docs were updated.

## Boundaries

- Never commit `.env`, API keys, or Supabase credentials.
- No frontend JS framework or CSS framework/library.
- No direct merges to `main`. Use a reviewed PR.
- Never alter an applied migration. Add a new one.
