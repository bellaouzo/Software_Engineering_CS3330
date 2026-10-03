-- Users log in with a username and password. Supabase Auth is email-based, so
-- the app signs users up with a placeholder email derived from the username and
-- passes the username in the signup metadata. The username lives on profiles.

alter table public.profiles
  add column username text;

alter table public.profiles
  add constraint profiles_username_format_check
  check (username ~ '^[a-z0-9_]{3,30}$');

-- Case-insensitive uniqueness. The format check already forces lowercase, but
-- the index keeps this true even if the check is ever loosened.
create unique index profiles_username_key
  on public.profiles (lower(username));

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, name, username)
  values (
    new.id,
    nullif(new.raw_user_meta_data ->> 'name', ''),
    nullif(lower(new.raw_user_meta_data ->> 'username'), '')
  );
  return new;
end;
$$;

revoke all on function public.handle_new_user() from public, anon, authenticated;
