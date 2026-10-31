#!/usr/bin/env python3
"""Fills a Supabase database with demo accounts, tickets, and comments.

    python seed_demo_data.py --db local              # local Docker Supabase
    python seed_demo_data.py --db live               # shared project (asks first)
    python seed_demo_data.py --db live --remove      # delete all demo data

Performance testing (TP-010), system testing (TP-012), and the final demo
(TP-013) all use this same data. Running it again rebuilds the demo tickets
from scratch and keeps the demo accounts, so it is safe to repeat.

Demo accounts are the usernames starting with "demo_". The script never
touches other users' tickets.

It uses the service-role key because it has to create accounts, make some of
them staff, and backdate tickets, which RLS correctly blocks for normal users.
The key is only read here, never by the app. Details: docs/guides/demo-data.md
"""

import argparse
import getpass
import os
import random
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import dev  # reuses the launcher's .env reader, Supabase CLI lookup, and prompts

try:
    from supabase import create_client
except ImportError:  # not running inside .venv yet: set it up, then rerun there
    dev.ensure_python_env()
    sys.exit(subprocess.call([str(dev.venv_python()), *sys.argv]))

from demo_content import COMMENTS, LOCATIONS, REQUESTERS, STAFF, TICKET_IDEAS
from routes.auth import PLACEHOLDER_EMAIL_DOMAIN, USERNAME_PATTERN
from routes.tickets import TICKET_STATUSES

DEFAULT_TICKET_COUNT = 120
RANDOM_SEED = 3300  # fixed, so every run builds the same tickets
DAYS_OF_HISTORY = 60
LOCAL_PASSWORD = "demo-password"  # local Docker database only
INSERT_BATCH_SIZE = 100


# ---------- building the demo rows (no database calls) ----------

def _pick_status(rng, age_days):
    """Older tickets are further along, like a real queue, with some mixing.

    Gives roughly a fifth Submitted and a quarter Closed, so both dashboards
    have something to show.
    """
    progress = age_days / DAYS_OF_HISTORY * 1.1 + (rng.random() - 0.5) * 0.3
    last = len(TICKET_STATUSES) - 1
    return TICKET_STATUSES[max(0, min(last, int(progress * len(TICKET_STATUSES))))]


def _comment_thread(rng, status, opened, requester_id, staff_id):
    """Comments that match how far the ticket got, oldest first.

    Returns (comments, last_status_change). Each step past Submitted gets a staff
    comment; sometimes the requester replies in between.
    """
    comments, when = [], opened
    if rng.random() < 0.3:
        when += timedelta(minutes=rng.randint(5, 90))
        comments.append((requester_id, rng.choice(COMMENTS["Requester"]), when))
    last_change = opened
    for step in TICKET_STATUSES[1:TICKET_STATUSES.index(status) + 1]:
        when += timedelta(hours=rng.randint(1, 30))
        last_change = when
        comments.append((staff_id, rng.choice(COMMENTS[step]), when))
        if step != "Closed" and rng.random() < 0.4:
            when += timedelta(minutes=rng.randint(10, 300))
            comments.append((requester_id, rng.choice(COMMENTS["Requester"]), when))
    return comments, last_change


def build_tickets(requester_ids, staff_ids, count, now):
    """Returns the same list of demo tickets every run, as dicts ready to insert.

    Each dict has a "comments" list of (user_id, text, time); the rest are
    tickets columns.
    """
    rng = random.Random(RANDOM_SEED)
    tickets = []
    for _ in range(count):
        category = rng.choice(sorted(TICKET_IDEAS))
        title, description = rng.choice(TICKET_IDEAS[category])
        age_days = rng.uniform(0.2, DAYS_OF_HISTORY)
        opened = now - timedelta(days=age_days)
        status = _pick_status(rng, age_days)
        requester_id = rng.choice(requester_ids)
        comments, last_change = _comment_thread(
            rng, status, opened, requester_id, rng.choice(staff_ids))
        # Keep everything in the past, even for brand-new tickets
        shift = max(timedelta(0), max([last_change] + [c[2] for c in comments]) - now)
        tickets.append({
            "title": title,
            "description": description,
            "location": rng.choice(LOCATIONS),
            "category": category,
            "status": status,
            "created_by": requester_id,
            "updated_at": (last_change - shift).isoformat(),
            "comments": [(user, text, when - shift) for user, text, when in comments],
        })
    return tickets


# ---------- talking to Supabase ----------

def _admin_client(db_mode):
    """Returns a service-role client, or exits with what is missing."""
    if db_mode == "local":
        sb = dev.supabase_cmd()
        status = dev.local_status(sb) if sb else None
        if not status:
            dev.fail("Local Supabase isn't running. Start it with: python dev.py --db local --keep-db")
            sys.exit(1)
        url = status.get("API_URL")
        key = status.get("SERVICE_ROLE_KEY") or status.get("SECRET_KEY")
    else:
        values = dev.read_dotenv()
        url, key = values.get("SUPABASE_URL"), values.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            dev.fail("Your .env needs SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY for the live database.")
            dev.info("Ask a teammate for the service-role key. Never commit it.")
            sys.exit(1)
    return create_client(url, key)


def _find_profile_id(client, username):
    result = client.table("profiles").select("id").eq("username", username).execute()
    return result.data[0]["id"] if result.data else None


def ensure_account(client, username, name, role, password):
    """Creates the account (or resets its password) and sets its role. Returns its id."""
    assert USERNAME_PATTERN.match(username), username
    user_id = _find_profile_id(client, username)
    if user_id:
        client.auth.admin.update_user_by_id(user_id, {"password": password})
    else:
        created = client.auth.admin.create_user({
            "email": f"{username}@{PLACEHOLDER_EMAIL_DOMAIN}",
            "password": password,
            "email_confirm": True,
            "user_metadata": {"name": name, "username": username},
        })
        user_id = created.user.id  # handle_new_user() makes the profiles row
    client.table("profiles").update({"name": name, "role": role}).eq("id", user_id).execute()
    return user_id


def clear_demo_tickets(client, demo_ids):
    """Deletes demo users' comments and tickets (their tickets' comments go too)."""
    client.table("comments").delete().in_("user_id", demo_ids).execute()
    client.table("tickets").delete().in_("created_by", demo_ids).execute()


def _insert_in_batches(client, table, rows):
    inserted = []
    for start in range(0, len(rows), INSERT_BATCH_SIZE):
        batch = rows[start:start + INSERT_BATCH_SIZE]
        inserted += client.table(table).insert(batch).execute().data
    return inserted


def insert_tickets(client, tickets):
    """Inserts the tickets, then their comments. Returns (tickets, comments) counts."""
    rows = [{k: v for k, v in t.items() if k != "comments"} for t in tickets]
    created = _insert_in_batches(client, "tickets", rows)
    comment_rows = [
        {"ticket_id": row["id"], "user_id": user, "text": text, "timestamp": when.isoformat()}
        for row, ticket in zip(created, tickets)
        for user, text, when in ticket["comments"]
    ]
    _insert_in_batches(client, "comments", comment_rows)
    return len(created), len(comment_rows)


def remove_demo_data(client):
    """Deletes every demo ticket, comment, and account."""
    usernames = [u for u, _ in REQUESTERS + STAFF]
    ids = [i for i in (_find_profile_id(client, u) for u in usernames) if i]
    if ids:
        clear_demo_tickets(client, ids)
        for user_id in ids:
            client.auth.admin.delete_user(user_id)  # profiles row goes with it
    dev.ok(f"Removed {len(ids)} demo accounts and their tickets")


# ---------- command line ----------

def _demo_password(db_mode):
    if db_mode == "local":
        return LOCAL_PASSWORD
    password = os.environ.get("DEMO_PASSWORD") or dev.read_dotenv().get("DEMO_PASSWORD")
    while not password or len(password) < 8:
        password = getpass.getpass("  Password for the demo accounts (8+ characters): ")
    return password


def seed(client, db_mode, count):
    password = _demo_password(db_mode)
    requester_ids = [ensure_account(client, u, n, "requester", password) for u, n in REQUESTERS]
    staff_ids = [ensure_account(client, u, n, "staff", password) for u, n in STAFF]
    dev.ok(f"{len(REQUESTERS)} requester and {len(STAFF)} staff demo accounts ready")
    clear_demo_tickets(client, requester_ids + staff_ids)
    tickets = build_tickets(requester_ids, staff_ids, count, datetime.now(timezone.utc))
    ticket_count, comment_count = insert_tickets(client, tickets)
    dev.ok(f"Inserted {ticket_count} tickets and {comment_count} comments")
    dev.info(f"Log in as {REQUESTERS[0][0]} (requester) or {STAFF[0][0]} (staff).")
    if db_mode == "local":
        dev.info(f"Password for every demo account: {LOCAL_PASSWORD}")


def main():
    parser = argparse.ArgumentParser(description="Add or remove demo data.")
    parser.add_argument("--db", choices=["local", "live"], required=True)
    parser.add_argument("--tickets", type=int, default=DEFAULT_TICKET_COUNT,
                        help=f"how many demo tickets (default {DEFAULT_TICKET_COUNT})")
    parser.add_argument("--remove", action="store_true", help="delete all demo data instead")
    parser.add_argument("--yes", action="store_true", help="skip the live database question")
    args = parser.parse_args()

    dev.header(f"Demo data ({args.db} database)")
    if args.db == "live" and not args.yes:
        dev.warn("The live database is shared by the whole team and the deployed site.")
        if not dev.ask_yes_no("Change demo data on the LIVE database?", default=False):
            return
    client = _admin_client(args.db)
    if args.remove:
        remove_demo_data(client)
    else:
        seed(client, args.db, args.tickets)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
