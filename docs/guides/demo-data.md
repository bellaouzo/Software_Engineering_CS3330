# Demo data

Summary in `AGENTS.md` > Quick start. Branch plan: `feature/be-seed-demo-data`
(supports Req 5.1 and the final demo).

`seed_demo_data.py` fills a database with demo accounts, tickets, and comments
so performance testing (TP-010), system testing (TP-012), and the final demo
(TP-013) all use the same data. The words it uses (names, ticket ideas,
comments) live in `demo_content.py`.

## Running it

```
python seed_demo_data.py --db local              # local Docker Supabase
python seed_demo_data.py --db live               # shared project, asks first
python seed_demo_data.py --db live --remove      # delete all demo data
python seed_demo_data.py --db local --tickets 500   # more tickets for load testing
```

- Plain `python` is fine: if the packages aren't installed yet, it sets up
  `.venv` (like `dev.py`) and reruns itself there.
- **Local:** start the database first and leave it running, e.g.
  `python dev.py --db local --keep-db`. The script reads the local service-role
  key from `supabase status`, so `.env` isn't needed. Every demo account's
  password is `demo-password`. A `supabase db reset` wipes the demo data; run
  the script again.
- **Live:** `.env` needs `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` (Supabase
  dashboard > Project Settings > API Keys; ask a teammate). The demo password
  comes from `DEMO_PASSWORD` in `.env`, or the script asks for one (8+
  characters). Share it with the team, not in the repo.

## What it makes

- Accounts (from `demo_content.py`): `demo_requester` to `demo_requester5`
  (requesters) and `demo_staff`, `demo_staff2` (staff). Log in with those
  usernames.
- 120 tickets by default, spread over the last 60 days, in every category and
  status. Older tickets are further along. Each status past Submitted has a
  staff comment, and requesters sometimes reply, all in time order.
- The tickets are the same every run (fixed random seed). Only the dates move,
  so they stay relative to today.

## Running it again

The script is safe to repeat. Existing demo accounts are kept (their password is
reset to the current one and their role set again). All tickets and comments
by demo accounts are deleted and rebuilt. Nobody else's tickets or comments are
touched.

`--remove` deletes the demo tickets, comments, and accounts. Do this on the live
database after the final demo if the team wants it clean.

## Why it uses the service-role key

Creating accounts, making some of them staff, and backdating tickets are all
blocked by RLS for normal users, which is correct for the app. This script is an
admin tool a teammate runs by hand, so it uses the service-role key. The app
itself never reads `SUPABASE_SERVICE_ROLE_KEY`; routes still query as the user
with `get_user_client()` (see `auth-helpers-examples.md`). Never commit the key.

## Changing the data

- Edit `demo_content.py` for names, locations, ticket ideas, and comment text.
  Categories must match `TICKET_CATEGORIES` and the comment keys must match
  `TICKET_STATUSES` (both in `routes/tickets.py`). Keep the wording generic: no
  product or school names.
- Edit `DEFAULT_TICKET_COUNT`, `DAYS_OF_HISTORY`, or `RANDOM_SEED` at the top of
  `seed_demo_data.py` for size and spread. Changing `RANDOM_SEED` changes every
  ticket, so tell whoever is running TP-010 to TP-013.
