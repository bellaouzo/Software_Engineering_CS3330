create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, name)
  values (
    new.id,
    nullif(new.raw_user_meta_data ->> 'name', '')
  );
  return new;
end;
$$;

revoke all on function public.handle_new_user() from public, anon, authenticated;

revoke update on public.profiles from authenticated;
grant update (name) on public.profiles to authenticated;

alter table public.profiles drop column email;
