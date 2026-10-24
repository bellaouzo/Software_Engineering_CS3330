# Database schema (Supabase)

Summary in `AGENTS.md` > Key rules. The source of truth is always
`supabase/migrations/`; if this file and a migration disagree, the migration
wins and this file needs fixing.

## Tables

- `profiles`: id (matches Supabase Auth id), name, username (unique, lowercase
  `a-z0-9_`, 3-30 chars; set from signup metadata by `handle_new_user()`),
  role (`"requester"` | `"staff"`).
  **No** `email` **column** — it was intentionally dropped (duplicate of Supabase
  Auth's own copy); don't re-add it without a reason.
- `tickets`: id, title, description, location, category, status, created_by,
  updated_at (auto-set by trigger on every update — don't set it manually).
- `comments`: id, ticket_id, user_id, text, timestamp.

## Triggers

A `handle_new_user()` trigger auto-creates a `profiles` row (default role
`'requester'`) whenever someone signs up via Supabase Auth — don't duplicate
this logic in `auth.py`.

## Row-Level Security

RLS is enabled on all three tables with real policies (see the migrations for
exact rules). Don't bypass RLS from app code by using the service-role key for
normal user requests — query with `get_user_client()` instead (see
`auth-helpers-examples.md`).

### Known issue — do not treat as correct, scheduled to be fixed during testing

The `tickets` UPDATE policy currently allows the ticket's own creator (not just
staff) to update it, which would let a requester change their own ticket's status.
Per Req 2.3.1, status changes should be staff-only. This is a known gap,
intentionally left for the team's test phase (it doubles as a real test case) —
don't copy this pattern elsewhere, and don't "fix" it without checking with the
team first, since it's being tracked deliberately.

## No status history table

Status changes just update `tickets.status` and `tickets.updated_at` directly.
Historical notes belong in `comments`, not a new table.

## Migrations

- Any schema change goes in a new migration. Create it with
  `supabase migration new <descriptive_name>`, which produces
  `YYYYMMDDHHMMSS_descriptive_name.sql` (e.g.
  `20260926005830_drop_profiles_email.sql`). Never rename or renumber by hand.
- Don't alter existing migrations after they've been applied — add a new
  migration file instead, even for small fixes (including the known RLS issue
  above, when the team is ready to fix it).
- Seed data (tickets/comments) lives in `supabase/seed.sql`; profiles come from
  the auth trigger, not the seed.

Database naming rules are in `naming-conventions.md`.
