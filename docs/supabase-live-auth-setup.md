# Live Supabase setup for login and registration

Login and registration use Supabase Auth with a username and password. Supabase
Auth is email-based, so the app maps each username to a placeholder email
(`<username>@tickets.invalid`) that never receives mail. Local Supabase
(`python dev.py --db local`) already works this way. The shared **live** project
needs the steps below once, before anyone registers on it.

## Checklist

1. **Apply the username migration.** `20261002190025_add_profiles_username.sql`
   adds `profiles.username` and updates `handle_new_user()`. Without it,
   registering creates accounts with no username. From the repo root, with the
   Supabase CLI logged in and linked to the live project:
   `supabase db push`. Check the Table Editor afterward: `profiles` should have a
   `username` column.
2. **Turn off "Confirm email".** Dashboard > Authentication > Sign In / Providers
   > Email > "Confirm email" off. With it on, new accounts wait for a
   confirmation link sent to the placeholder address, so nobody can log in.
3. **Check the password length.** Dashboard > Authentication > Sign In /
   Providers > "Minimum password length". The app shows a "too weak" message when
   Supabase rejects a password, so any value works. Local uses 6.
4. **Confirm the placeholder email is accepted.** Register one test account on
   live. If Supabase answers with an invalid-email error, change
   `PLACEHOLDER_EMAIL_DOMAIN` in `routes/auth.py` to a domain it accepts, and
   update the matching line in `AGENTS.md`.
5. **Do a real pass.** Register a new username, log in with it, confirm
   `profiles` shows the name and username with role `requester`, then try a wrong
   password and a username that is already taken.
6. **Check Render's environment.** `FLASK_SECRET_KEY`, `SUPABASE_URL`, and
   `SUPABASE_KEY` (the anon/publishable key, never the service-role key) must be
   set. The secret key has to be a real random value, or sessions are not safe.

## Making someone staff

New accounts are always `requester`. Promote a user in the Table Editor by
changing `role` to `staff` on their `profiles` row, or run in the SQL Editor:

```sql
update public.profiles set role = 'staff' where username = 'their_username';
```

## Updating this file

If auth setup changes (new migration, new Supabase setting, new env var), update
this checklist in the same branch.
