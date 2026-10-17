-- F-004: policies added by hand on the live project let every logged-in user
-- read and change every ticket, comment, and profile. Policies are OR'd
-- together, so these overrode the real ones. Drop them so only the policies
-- from 20260926005657_create_ticketing_tables.sql apply.
drop policy if exists "Allow invited users full access to tickets" on public.tickets;
drop policy if exists "Logged-in users have full access" on public.tickets;

drop policy if exists "Allow invited users full access to comments" on public.comments;
drop policy if exists "Logged-in users have full access" on public.comments;

drop policy if exists "Allow invited users full access to profiles" on public.profiles;
drop policy if exists "Logged-in users have full access" on public.profiles;
