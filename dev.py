#!/usr/bin/env python3
"""One-command launcher for local development.

    python dev.py

Asks which database to use (local Docker Supabase or the live hosted one),
makes sure everything needed is set up, starts the Flask app, and opens the
page you pick in your browser. Uses only the Python standard library so it can
run before the virtual environment exists.

Skip the questions with flags, e.g.:
    python dev.py --db local --open tickets
"""

import argparse
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
APP_URL = "http://127.0.0.1:5000"
DEFAULT_STUDIO_URL = "http://127.0.0.1:54323"

PAGES = {
    "dashboard": ("Dashboard", "/dashboard"),
    "login": ("Log in", "/login"),
    "register": ("Create account", "/register"),
    "tickets": ("Ticket list", "/tickets"),
    "new-ticket": ("New ticket form", "/tickets/new"),
}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if os.name == "nt":
    os.system("")  # turns on ANSI colors in the Windows console

_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ


def _c(code, text):
    return f"\033[{code}m{text}\033[0m" if _COLOR else text


def bold(t): return _c("1", t)
def dim(t): return _c("2", t)
def green(t): return _c("32", t)
def yellow(t): return _c("33", t)
def red(t): return _c("31", t)
def cyan(t): return _c("36", t)


def header(text):
    print()
    print(cyan(bold(f"== {text} ==")))


def info(text): print(f"  {text}")
def ok(text): print(f"  {green('OK')} {text}")
def warn(text): print(f"  {yellow('!')} {text}")
def fail(text): print(f"  {red('X')} {text}")


def ask(prompt, default=None):
    suffix = f" [{default}]" if default else ""
    try:
        answer = input(f"{bold(prompt)}{suffix}: ").strip()
    except EOFError:
        raise SystemExit("\nNo input available; use flags (see --help).")
    return answer or (default or "")


def ask_yes_no(prompt, default=True):
    hint = "Y/n" if default else "y/N"
    while True:
        answer = ask(f"{prompt} ({hint})").lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False


def ask_choice(prompt, options, default=1):
    """options: list of (key, label). Returns the chosen key."""
    print(bold(prompt))
    for i, (_, label) in enumerate(options, 1):
        print(f"  {cyan(str(i))}) {label}")
    while True:
        answer = ask("Enter a number", str(default))
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1][0]
        warn(f"Please enter a number from 1 to {len(options)}.")


def run(cmd, env=None, check=False):
    return subprocess.run(cmd, cwd=ROOT, env=env, check=check)


def capture(cmd, env=None):
    return subprocess.run(
        cmd, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


# --------------------------------------------------------------------- Python

def venv_python():
    sub = "Scripts/python.exe" if os.name == "nt" else "bin/python"
    return VENV / sub


def ensure_python_env():
    header("Python environment")
    if sys.version_info < (3, 10):
        fail(f"Python {sys.version.split()[0]} is too old. Install Python 3.10+ (the project uses 3.14).")
        raise SystemExit(1)
    py = venv_python()
    if not py.exists():
        info("No virtual environment yet - creating .venv (one time only)...")
        run([sys.executable, "-m", "venv", str(VENV)], check=True)
    if capture([str(py), "-m", "pip", "--version"]).returncode != 0:
        info("This .venv has no pip (it was probably made by another tool) - adding it...")
        if capture([str(py), "-m", "ensurepip", "--upgrade"]).returncode != 0:
            fail("Couldn't add pip. Delete the .venv folder and run this again to rebuild it.")
            raise SystemExit(1)
    info("Checking packages from requirements.txt...")
    result = capture([str(py), "-m", "pip", "install", "-q", "-r", "requirements.txt"])
    if result.returncode != 0:
        fail("Installing packages failed:")
        print(result.stderr or result.stdout)
        raise SystemExit(1)
    ok("Python environment ready")
    return py


# --------------------------------------------------------------------- Docker

def docker_state():
    """Returns 'missing', 'stopped' or 'running'."""
    if not shutil.which("docker"):
        return "missing"
    result = capture(["docker", "info"])
    return "running" if result.returncode == 0 else "stopped"


def docker_help(state):
    if state == "missing":
        fail("Docker isn't installed on this computer.")
        info("Docker runs the local database. Install Docker Desktop, then run this again:")
        if os.name == "nt":
            info(f"  Windows: {cyan('winget install Docker.DockerDesktop')}")
            info("           or download from https://www.docker.com/products/docker-desktop/")
        elif sys.platform == "darwin":
            info(f"  Mac:     {cyan('brew install --cask docker')}")
            info("           or download from https://www.docker.com/products/docker-desktop/")
        else:
            info("  Linux:   https://docs.docker.com/engine/install/")
        info("After installing, open Docker Desktop once and let it finish starting.")
    else:
        fail("Docker is installed but not running.")
        info("Open Docker Desktop and wait until it says the engine is running")
        info("(the whale icon in the tray stops animating - can take a minute or two).")


def ensure_docker():
    """Returns True when Docker is ready, False if the user wants the live DB instead."""
    header("Docker")
    while True:
        state = docker_state()
        if state == "running":
            ok("Docker is running")
            return True
        docker_help(state)
        print()
        choice = ask_choice(
            "What now?",
            [
                ("retry", "I fixed it - check again"),
                ("live", "Use the live database instead (no Docker needed)"),
                ("quit", "Quit"),
            ],
        )
        if choice == "live":
            return False
        if choice == "quit":
            raise SystemExit(0)


# ------------------------------------------------------------------- Supabase

def supabase_cmd():
    """Returns the command prefix for the Supabase CLI, or None."""
    if shutil.which("supabase"):
        return ["supabase"]
    if shutil.which("npx"):
        return [shutil.which("npx"), "--yes", "supabase@latest"]
    return None


def supabase_help():
    fail("The Supabase CLI isn't available.")
    info("Easiest fix: install Node.js (https://nodejs.org) - this launcher then uses")
    info("`npx supabase` automatically, nothing else to install.")
    if os.name == "nt":
        info("Or install the CLI with Scoop:")
        info(cyan("  scoop bucket add supabase https://github.com/supabase/scoop-bucket.git"))
        info(cyan("  scoop install supabase"))
    elif sys.platform == "darwin":
        info(f"Or: {cyan('brew install supabase/tap/supabase')}")
    else:
        info("Or see https://supabase.com/docs/guides/local-development/cli/getting-started")


def parse_env_output(text):
    values = {}
    for line in text.splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def local_status(sb):
    result = capture(sb + ["status", "-o", "env"])
    if result.returncode != 0:
        return None
    return parse_env_output(result.stdout)


def start_local_db():
    """Starts local Supabase. Returns (env_for_flask, studio_url)."""
    sb = supabase_cmd()
    if sb is None:
        supabase_help()
        raise SystemExit(1)

    header("Local database")
    status = local_status(sb)
    was_running = status is not None
    if was_running:
        ok("Local Supabase is already running")
    else:
        info("Starting local Supabase in Docker.")
        info(dim("First time takes a few minutes while Docker downloads images."))
        print()
        if run(sb + ["start"]).returncode != 0:
            fail("Supabase failed to start. Scroll up for the error, or run with Docker Desktop open.")
            raise SystemExit(1)
        status = local_status(sb)
        if status is None:
            fail("Supabase started but its status couldn't be read.")
            raise SystemExit(1)
        ok("Local Supabase started")

    print()
    info("A reset rebuilds your local database from scratch using the project's")
    info("latest database files, then adds the sample data.")
    info(f"  {green('Say yes')} if this is your first time, or you just pulled new changes")
    info("  (someone changed the database, e.g. added a column).")
    info(f"  {yellow('Say no')} to keep the test accounts and tickets you already made.")
    info(dim("It only affects the local copy on your computer, never the live database."))
    if ask_yes_no("Reset the local database?", default=not was_running):
        print()
        if run(sb + ["db", "reset"]).returncode != 0:
            fail("Database reset failed. Scroll up for the error.")
            raise SystemExit(1)
        ok("Local database reset")

    url = status.get("API_URL")
    key = status.get("ANON_KEY") or status.get("PUBLISHABLE_KEY")
    if not url or not key:
        fail("Couldn't find the local API URL / anon key in `supabase status` output.")
        raise SystemExit(1)
    env = {"SUPABASE_URL": url, "SUPABASE_KEY": key}
    return env, status.get("STUDIO_URL", DEFAULT_STUDIO_URL)


def stop_local_db():
    sb = supabase_cmd()
    if sb:
        info("Stopping local Supabase...")
        run(sb + ["stop"])


# ------------------------------------------------------------------- Live DB

def read_dotenv():
    values = {}
    path = ROOT / ".env"
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def use_live_db():
    """Returns env_for_flask, or None if the user backed out."""
    header("Live database")
    values = read_dotenv()
    missing = [k for k in ("SUPABASE_URL", "SUPABASE_KEY") if not values.get(k)]
    if missing:
        fail(f"Your .env file is missing: {', '.join(missing)}")
        info("Copy .env.example to .env and ask a teammate for the real values.")
        info("(Don't make up your own, and never commit the .env file.)")
        return None
    ok(f"Found live credentials in .env ({values['SUPABASE_URL']})")
    warn("The live database is shared. Anything you create, change, or delete")
    warn("while testing affects the whole team.")
    if not ask_yes_no("Continue with the LIVE database?", default=False):
        return None
    env = {"SUPABASE_URL": values["SUPABASE_URL"], "SUPABASE_KEY": values["SUPABASE_KEY"]}
    if values.get("FLASK_SECRET_KEY"):
        env["FLASK_SECRET_KEY"] = values["FLASK_SECRET_KEY"]
    return env


# ----------------------------------------------------------------------- Run

def open_when_ready(url):
    def worker():
        for _ in range(60):
            try:
                urllib.request.urlopen(f"{APP_URL}/health", timeout=1)
                break
            except Exception:
                time.sleep(0.5)
        else:
            return
        webbrowser.open(url)

    threading.Thread(target=worker, daemon=True).start()


def run_app(py, env, open_url):
    header("Starting the app")
    info(f"App:  {cyan(APP_URL)}")
    info(dim("Press Ctrl+C to stop."))
    print()
    child_env = {**os.environ, **env}
    if open_url:
        open_when_ready(open_url)
    try:
        run([str(py), "app.py"], env=child_env)
    except KeyboardInterrupt:
        pass
    print()
    info("App stopped.")


def choose_page(db_mode, studio_url, flag):
    if flag:
        if flag == "studio":
            return studio_url if db_mode == "local" else None
        if flag == "none":
            return None
        return APP_URL + PAGES[flag][1]
    header("Where to?")
    options = [(APP_URL + path, f"{label}  {dim(path)}") for label, path in PAGES.values()]
    if db_mode == "local":
        options.append((studio_url, f"Supabase Studio (browse the local database)  {dim(studio_url)}"))
    options.append((None, "Don't open anything"))
    return ask_choice("Which page should open in your browser?", options, default=1)


def connect_database(db_mode):
    """Gets a working database. Returns (db_mode, env_for_flask, studio_url)."""
    while True:
        if db_mode == "local":
            if ensure_docker():
                env, studio_url = start_local_db()
                return db_mode, env, studio_url
            db_mode = "live"  # no Docker; the user chose the live DB instead
        env = use_live_db()
        if env is not None:
            return db_mode, env, DEFAULT_STUDIO_URL
        print()
        if not ask_yes_no("Use the local (Docker) database instead?", default=True):
            raise SystemExit(0)
        db_mode = "local"


def main():
    parser = argparse.ArgumentParser(description="Run the ticketing app locally.")
    parser.add_argument("--db", choices=["local", "live"], help="skip the database question")
    parser.add_argument(
        "--open",
        choices=[*PAGES, "studio", "none"],
        help="skip the 'where to?' question",
    )
    parser.add_argument("--keep-db", action="store_true", help="leave local Supabase running on exit")
    args = parser.parse_args()

    print(bold(cyan("\nCS 3300 Ticketing - local launcher")))

    db_mode = args.db
    if not db_mode:
        print()
        db_mode = ask_choice(
            "Which database do you want to use?",
            [
                ("local", f"Local   {dim('- private copy in Docker; safe to break (recommended)')}"),
                ("live", f"Live    {dim('- the shared Supabase project; changes affect the team')}"),
            ],
        )

    db_mode, env, studio_url = connect_database(db_mode)
    py = ensure_python_env()
    page = choose_page(db_mode, studio_url, args.open)
    run_app(py, env, page)

    if db_mode == "local" and not args.keep_db:
        print()
        if ask_yes_no("Stop the local database containers too?", default=False):
            stop_local_db()
        else:
            info("Leaving local Supabase running (stop it later with: supabase stop).")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
