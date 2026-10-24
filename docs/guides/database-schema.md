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

### Ticket updates are staff-only

`tickets` UPDATE is allowed for staff only (`"Staff update tickets"`, from
`20261024000711_staff_only_ticket_updates.sql`, fixing F-001 / Req 2.3.1, 4.1).
It replaced the old "Creators and staff update tickets" policy, which let a
requester change their own ticket's status. Requesters can still insert and read
their own tickets. Don't add a creator clause back to the update policy.

## No status history table

Status changes just update `tickets.status` and `tickets.updated_at` directly.
Historical notes belong in `comments`, not a new table.

## Migrations

- Any schema change goes in a new migration. Create it with
  `supabase migration new <descriptive_name>`, which produces
  `YYYYMMDDHHMMSS_descriptive_name.sql` (e.g.
  `20260926005830_drop_profiles_email.sql`). Never rename or renumber by hand.
- Don't alter existing migrations after they've been applied — add a new
  migration file instead, even for small fixes.
- Seed data (tickets/comments) lives in `supabase/seed.sql`; profiles come from
  the auth trigger, not the seed.

Database naming rules are in `naming-conventions.md`.
