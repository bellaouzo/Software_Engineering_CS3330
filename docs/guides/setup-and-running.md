# Setup and running locally

Summary in `AGENTS.md` > Quick start. This is the full version.

## Easiest way: one command

```
python dev.py        # macOS/Linux: python3 dev.py
```

`dev.py` is an interactive launcher. It asks which database to use — **Local**
(a private Supabase running in Docker, safe to break) or **Live** (the shared
Supabase project, using the credentials in `.env`) — then sets up `.venv` and
installs `requirements.txt`, starts the Flask app, and opens the page you pick
in your browser.

- If you pick Local and Docker isn't installed or running, it explains how to
  fix that (or lets you switch to Live).
- Local mode needs Docker Desktop; it uses the `supabase` CLI if installed,
  otherwise `npx supabase` (needs Node.js).
- Flags skip the questions: `--db local|live`,
  `--open dashboard|login|register|tickets|new-ticket|studio|none`, `--keep-db`.
- When the app exits in Local mode, it asks whether to stop the database
  containers; the default answer is yes (press Enter), and `--keep-db` skips the
  question and leaves them running.
- It passes the Supabase URL/key to the app through environment variables only —
  it never writes keys to disk.

**AI agents:** to run the app for a user, use `python dev.py` (with flags if you
must avoid prompts) instead of hand-rolling these steps, and warn before
choosing the Live database.

## Manual way

```
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Requires a local `.env` file (see `.env.example` for the shape) with
`FLASK_SECRET_KEY`, `SUPABASE_URL`, and `SUPABASE_KEY` — never commit this file.
Ask a teammate for the real values; do not generate or guess your own.

## Git and GitHub prerequisites

Everyone (and their AI tool) needs these to use the branch/PR workflow in
`git-workflow.md`:

- **Git** installed (`git --version`), with `user.name` and `user.email` set.
- **Access to the GitHub repo** (accepted collaborator invite) and the ability to
  push to it.
- **GitHub CLI (`gh`)** installed and logged in (`gh auth login`) so an AI can
  open PRs from the terminal. Optional: without it, push the branch and open the
  PR from the link Git prints or the "Compare & pull request" button on GitHub.

If a prerequisite is missing, an AI agent should tell the user what's missing and
how to fix it rather than failing silently or working around it.

## Demo data

To fill a database with demo accounts and tickets, see `demo-data.md`
(`python seed_demo_data.py --db local`).

## Live Supabase

One-time steps on the shared Supabase project for login and registration are in
`supabase-live-auth-setup.md`.
