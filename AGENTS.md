# [AGENTS.md](http://AGENTS.md)

## Project overview

A web-based maintenance ticketing system built for UCCS CS 3300 (Intro to Software
Engineering). Two roles: **Requester** (submits and tracks tickets) and **Staff**
(reviews, updates status, resolves tickets). Both can comment on a ticket.

## Tech stack

- **Python 3.14** (pinned in `runtime.txt` as python-3.14.7) + **Flask** for routing and backend logic
- **Jinja2** (built into Flask) for server-rendered HTML templates
- **Supabase** (hosted Postgres + Auth) for the database and login
- **Render** for hosting/deployment (auto-deploys from GitHub)
- Raw HTML/CSS/JS in the browser — no frontend framework (React, Vue, etc.) and
  no CSS framework or library either (Bootstrap, Pico.css, Tailwind, etc.).
  Write our own CSS in `static/css/app.css`.

## Setup & running locally

**Easiest way — one command:**

```
python dev.py        # macOS/Linux: python3 dev.py
```

`dev.py` is an interactive launcher. It asks which database to use — **Local**
(a private Supabase running in Docker, safe to break) or **Live** (the shared
Supabase project, using the credentials in `.env`) — then sets up `.venv` and
installs `requirements.txt`, starts the Flask app, and opens the page you pick
in your browser. If you pick Local and Docker isn't installed or running, it
explains how to fix that (or lets you switch to Live). Local mode needs Docker
Desktop; it uses the `supabase` CLI if installed, otherwise `npx supabase`
(needs Node.js). Flags skip the questions: `--db local|live`,
`--open dashboard|login|register|tickets|new-ticket|studio|none`, `--keep-db`.
When the app exits in Local mode, it asks whether to stop the database
containers; the default answer is yes (press Enter), and `--keep-db` skips the
question and leaves them running. It passes the Supabase URL/key to the app through environment variables only —
it never writes keys to disk. **AI agents:** to run the app for a user, use
`python dev.py` (with flags if you must avoid prompts) instead of hand-rolling
these steps, and warn before choosing the Live database.

**Manual way:**

```
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Requires a local `.env` file (see `.env.example` for the shape) with
`FLASK_SECRET_KEY`, `SUPABASE_URL`, and `SUPABASE_KEY` — never commit this file.
Ask a teammate for the real values; do not generate or guess your own.

### Git & GitHub prerequisites

Everyone (and their AI tool) needs these to use the branch/PR workflow below:

- **Git** installed (`git --version`), with `user.name` and `user.email` set.
- **Access to the GitHub repo** (accepted collaborator invite) and the ability to
  push to it.
- **GitHub CLI (`gh`)** installed and logged in (`gh auth login`) so an AI can
  open PRs from the terminal. Optional: without it, push the branch and open the
  PR from the link Git prints or the "Compare & pull request" button on GitHub.

If a prerequisite is missing, an AI agent should tell the user what's missing and
how to fix it rather than failing silently or working around it.

## Folder structure

```
app.py                  # Flask app factory (create_app), loads .env, registers routes, /health check
dev.py                  # One-command interactive launcher (pick local/live DB, start app, open browser)
supabase_client.py      # get_supabase_client() (anon) and get_user_client() (acts as the logged-in user, RLS applies)
auth_helpers.py         # @require_login and @require_staff decorators for route functions
routes/                 # BACK END - Flask Blueprints
  __init__.py            # register_routes(app) - wires up all blueprints
  auth.py                 # auth_bp: /login, /register, /logout
  tickets.py               # tickets_bp: /tickets, /tickets/new, /tickets/<id>
  dashboard.py              # dashboard_bp: / and /dashboard (both -> home)
templates/               # FRONT END - HTML + Jinja2, extend base.html
static/
  css/app.css
  js/app.js
supabase/
  migrations/             # Timestamp-named SQL migrations - the source of truth for schema
  seed.sql                 # Seed data (tickets/comments) - profiles come from auth triggers
  config.toml
docs/                    # Team documents (Word docs, PDFs, spreadsheets) - not code
```

Routes are registered as **Blueprints**, not flat route files — each blueprint
(`auth_bp`, `tickets_bp`, `dashboard_bp`) is registered once in `routes/__init__.py`.
A "page" still has two halves: the route function in `routes/<name>.py` (backend)
and the matching template in `templates/<name>.html` (frontend). Never put HTML in
a routes file or Supabase calls in a template.

## Database schema (Supabase) — source of truth is `supabase/migrations/`

- `profiles`: id (matches Supabase Auth id), name, username (unique, lowercase
  `a-z0-9_`, 3-30 chars; set from signup metadata by `handle_new_user()`),
  role ("requester"|"staff").
  **No** `email` **column** — it was intentionally dropped (duplicate of Supabase
  Auth's own copy); don't re-add it without a reason.
- `tickets`: id, title, description, location, category, status, created_by,
  updated_at (auto-set by trigger on every update — don't set it manually)
- `comments`: id, ticket_id, user_id, text, timestamp
- A `handle_new_user()` trigger auto-creates a `profiles` row (default role
  `'requester'`) whenever someone signs up via Supabase Auth — don't duplicate
  this logic in `auth.py`.
- Row-Level Security is already enabled on all three tables with real policies
  (see the migrations for exact rules) — don't bypass RLS from app code by using
  the service-role key for normal user requests.

### Known issue — do not treat as correct, scheduled to be fixed during testing

The `tickets` UPDATE policy currently allows the ticket's own creator (not just
staff) to update it, which would let a requester change their own ticket's status.
Per Req 2.3.1, status changes should be staff-only. This is a known gap, intentionally
left for the team's test phase (it doubles as a real test case) — don't copy this
pattern elsewhere, and don't "fix" it without checking with the team first, since
it's being tracked deliberately.

## Conventions

- Route functions handle both GET (show a form/page) and POST (process submitted
  data) in one function, per Flask convention — don't split these into two routes.
- Routes currently not wired to Supabase return a flash message saying so
  explicitly (e.g. "This ticket was not saved. The database is not connected
  yet."). When you wire one up, replace the stub flash message, don't leave it
  alongside real logic.
- Ticket status values are exactly: `Submitted`, `Acknowledged`, `In Progress`,
  `Resolved`, `Closed`. Don't introduce new status strings without updating the
  requirements spreadsheet first.
- No separate "status history" table — status changes just update `tickets.status`
  and `tickets.updated_at` directly. Historical notes belong in `comments`, not a
  new table.
- Users log in with a **username and password**, not an email. Supabase Auth is
  email-based, so `routes/auth.py` maps each username to a placeholder email
  (`<username>@tickets.invalid`, never emailed) and passes the username in signup
  metadata, where `handle_new_user()` copies it to `profiles.username`. Email
  confirmation must stay **off** in Supabase Auth settings, since the placeholder
  address can't receive mail. After login the Supabase `user_id`, `access_token`,
  and `refresh_token` are stored in the Flask `session`. Any schema change goes
  in a new migration.
- **Protecting routes and querying as the user:** put `@require_login` (or
  `@require_staff`) from `auth_helpers.py` under the route decorator. For any
  table query made on a user's behalf, use `get_user_client()` from
  `supabase_client.py` so RLS applies. Use `get_supabase_client()` only for
  calls with no logged-in user (login, register). Don't write your own session
  or token handling. Full examples (insert, staff-only, error handling) are in
  `docs/guides/auth-helpers-examples.md`. Live Supabase setup steps for auth are
  in `docs/guides/supabase-live-auth-setup.md`.

  ```python
  @tickets_bp.get("/tickets")
  @require_login          # directly under the route decorator
  def list_tickets():
      tickets = get_user_client().table("tickets").select("*").execute().data
      return render_template("tickets.html", tickets=tickets)
  ```
- When implementing a requirement, reference its ID from the requirements  
  spreadsheet in the commit message or PR description (e.g. "Implements 2.1.1").

## Naming conventions

**Python (back end)**
- Files/modules: `snake_case.py`. Functions/variables: `snake_case`, verb-first for
  functions (`create_ticket`, `get_ticket_by_id`, `update_ticket_status`).
- Classes: `PascalCase`. Constants: `UPPER_SNAKE_CASE` (e.g. `TICKET_STATUSES`).
- Blueprint objects: `<name>_bp` (`auth_bp`, `tickets_bp`).
- Route functions are named after the action (`list_tickets`, `new_ticket`,
  `ticket_detail`) — they double as `url_for` endpoints (`url_for("tickets.new_ticket")`,
  where the prefix is the short blueprint name, e.g. `Blueprint("tickets", ...)`),
  so keep them unique and descriptive.
- Private helpers get a leading underscore (`_require_staff()`).

**URLs**
- Lowercase, plural nouns, hyphens (not underscores) for multiple words:
  `/tickets`, `/tickets/new`, `/tickets/<ticket_id>`. Ticket IDs are UUIDs, not
  integers — never use `<int:...>` converters for them.

**Templates (Jinja2)**
- Files: `snake_case.html`, named after the page. `base.html` is the only layout.
- Partials live in `templates/partials/` and start with an underscore
  (`_ticket_card.html`, `_flash_messages.html`).
- Template variables: `snake_case`, matching the names passed from Python.
- Block names: short and lowercase (`title`, `content`, `scripts`).

**Database (Supabase/Postgres)**
- Tables: plural `snake_case`. Columns: singular `snake_case`.
- Foreign keys: `<thing>_id`. Who/when columns: `created_by`, `*_at`
  (e.g. `updated_at`). Prefer `created_at` over `timestamp` for new columns.
- Migrations: create with `supabase migration new <descriptive_name>`, which
  produces `YYYYMMDDHHMMSS_descriptive_name.sql` (e.g.
  `20260926005830_drop_profiles_email.sql`). Never rename or renumber by hand.
- Constraints, policies, triggers: descriptive names
  (e.g. `tickets_staff_update_policy`).

**CSS**
- Classes: `kebab-case`, BEM-style when nesting is needed: `.ticket-card`,
  `.ticket-card__title`, `.ticket-card--urgent`.
- State classes use `is-`/`has-` prefixes (`.is-active`, `.has-error`).
- CSS variables: `--color-primary`, `--space-md`.

**JavaScript**
- Variables/functions: `camelCase`. Constants: `UPPER_SNAKE_CASE`.
- Hook scripts to the DOM with `data-` attributes or `js-` prefixed classes
  (`.js-status-select`), never styling classes.
- Files: `kebab-case.js` (or `app.js`).

**Data values**
- Statuses use the exact strings listed under Conventions above. Roles are
  lowercase: `requester`, `staff`.
- Other user-facing enum-like values (e.g. category) use Title Case.

## Branching

- Name branches by feature, not by sprint: `feature/be-auth-supabase`,
  `feature/fe-polish`, etc. — never `feature/sprint1-...`. A branch's name
  describes what it does, not when it was planned, since work sometimes runs
  past a sprint boundary and renaming a branch breaks its PR history.
- Keep branches small enough to realistically merge within one sprint. If a
  branch is dragging, split it rather than letting it run long.
- Open PRs early (even as a draft) rather than only once "done," so review can
  happen incrementally.
- `main` is protected — no direct pushes, PRs required.

### When to start a new branch vs. keep working on the current one

Because this is a team project, **new work gets its own branch** — never pile
unrelated changes onto whatever branch happens to be checked out.

- **Start a new branch** when the work is a different feature, requirement, bug,
  or area than the current branch (e.g. moving from auth to ticket comments).
  Branch from an up-to-date `main`, not from the previous feature branch.
- **Stay on the current branch** when the work is the same concept or clearly
  related (follow-up fixes, tweaks, review feedback, more commits toward the same
  requirement). Don't create a branch per small change — extra commits on the
  same branch are fine, and the open PR updates automatically.
- If unsure, ask: "Could this be reviewed and merged on its own?" If yes, it's
  probably a new branch.
- **AI agents:** before making changes, check the current branch (`git branch
  --show-current`). If you're on `main`, or the task is unrelated to the branch's
  purpose, tell the user and create a new `feature/...` branch (per the naming
  rules above) instead of committing there. Never commit directly to `main`.

### Merging to `main` — the required workflow

`main` has a GitHub branch ruleset: changes can only land through a pull request
(PR) with the required approval, and the branch must be **up to date with the
latest `main`** before merging. Not everyone on the team is comfortable with
GitHub yet, so **when a user is ready to merge, don't assume they know the
steps. Offer to run each one for them, say in plain language what it does and
why, and show the result.** Run the commands yourself when the user agrees; if a
tool is missing (see Git & GitHub prerequisites), give them the manual
instruction or link instead. **Always ask for confirmation before the push and
before opening the PR** — those affect the shared repo.

1. **Commit your work** on your feature branch (message references the
   requirement ID, e.g. "Implements 2.1.1").
2. **Update your branch with the latest `main`** (the ruleset requires this):
   `git fetch origin`, then `git merge origin/main` (or `git rebase origin/main`
   if the team prefers). If there are conflicts, Git marks them in the files —
   help the user resolve them, then `git add` the files and finish the merge.
   Re-run the app to confirm it still works.
3. **Push the branch**: `git push -u origin <branch-name>` (first push) or
   `git push` afterwards.
4. **Open a pull request** on GitHub into `main` (the push output prints a link,
   or use the "Compare & pull request" button on the repo page, or
   `gh pr create`). Give it a clear title, mention the requirement ID(s) in the
   description, and say what changed and how to test it. Use **Draft** if it's
   not ready yet.
5. **Request a review** from your cross-functional testing pair (see Testing).
6. **Respond to feedback** by committing to the same branch and pushing — the PR
   updates itself. Don't open a new PR.
7. **Merge** once it's approved and shows as up to date with `main`. If GitHub
   says the branch is out of date, repeat step 2 and push again.
8. **Clean up**: switch back to `main`, `git pull`, and delete the merged branch
   (`git branch -d <branch-name>`). Start the next piece of work from this
   fresh `main`.

If a push to `main` is rejected, that's the ruleset working as intended — it
means the work needs to be on a feature branch and go through a PR.

## Testing

- Cross-functional rule: whoever wrote the Back End for a feature does not test
  its Front End, and vice versa — Front End writers test Back End work and Back
  End writers test Front End work.
- Test methods map to the requirements spreadsheet's T/A/I/O column: Test,
  Analysis, Inspection, Observation.
- Each test should be documented as its own numbered Test Plan, per the class
  Test Plan template — don't lump multiple tests into one plan.
- The known RLS issue above should become one of these test cases once the team  
  reaches testing.

## Keeping this file and the docs current

**AI agents:** this file is the shared source of truth for every teammate's AI, so
a stale entry misleads the whole team. After finishing any change, before the
final commit, update this file and any other affected docs **in the same branch**:

- New or moved files, helpers, or routes: update **Folder structure**.
- Schema, RLS, or migration changes: update **Database schema**.
- New conventions, decisions, or shared helpers: update **Conventions**.
- Setup, env vars, or run steps: update **Setup & running locally** and
  `.env.example`.
- Anything that needs manual steps on the live Supabase project: add or update a
  Markdown file in `docs/guides/`. Markdown goes in `docs/guides/`; Word docs,
  PDFs, and spreadsheets stay out of that folder (see `docs/README.md`).

Delete notes that are no longer true instead of leaving them beside the new
behavior. Say in the commit or PR description which docs were updated.

## Boundaries

- Never commit `.env`, API keys, or Supabase credentials — use environment
  variables only.
- Don't add a frontend JS framework (React/Vue/etc.) or a CSS framework/library
  (Bootstrap, Pico.css, Tailwind, etc.) — this project is server-rendered with
  raw HTML/CSS/JS by design.
- Don't merge directly to `main` — open a pull request and get it reviewed by
  your cross-functional testing pair first.
- Don't alter existing migrations after they've been applied — add a new
  migration file instead, even for small fixes (including the known RLS issue
  above, when the team is ready to fix it).
