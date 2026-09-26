-- Ticketing schema: profiles, tickets, and comments.

create schema if not exists private;

revoke all on schema private from public;
grant usage on schema private to authenticated;

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  name text,
  role text not null default 'requester' constraint profiles_role_check check (role in ('requester', 'staff'))
);

create table public.tickets (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  description text,
  location text,
  category text,
  status text not null default 'Submitted',
  created_by uuid not null references public.profiles (id) on delete restrict,
  updated_at timestamptz not null default now()
);

create table public.comments (
  id uuid primary key default gen_random_uuid(),
  ticket_id uuid not null references public.tickets (id) on delete cascade,
  user_id uuid not null references public.profiles (id) on delete restrict,
  text text not null,
  "timestamp" timestamptz not null default now()
);

create index tickets_created_by_idx on public.tickets (created_by);
create index tickets_status_idx on public.tickets (status);
create index comments_ticket_id_idx on public.comments (ticket_id);
create index comments_user_id_idx on public.comments (user_id);
create index comments_timestamp_idx on public.comments ("timestamp");

create or replace function private.is_staff()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.profiles
    where id = (select auth.uid())
      and role = 'staff'
  );
$$;

revoke all on function private.is_staff() from public;
grant execute on function private.is_staff() to authenticated;

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

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

create or replace function public.set_tickets_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger tickets_set_updated_at
  before update on public.tickets
  for each row execute function public.set_tickets_updated_at();

revoke all on function public.handle_new_user() from public, anon, authenticated;
revoke all on function public.set_tickets_updated_at() from public, anon, authenticated;

grant select on public.profiles to authenticated;
grant update (name) on public.profiles to authenticated;
grant select, insert, update, delete on public.profiles to service_role;

grant select, insert, update on public.tickets to authenticated;
grant select, insert, update, delete on public.tickets to service_role;

grant select, insert on public.comments to authenticated;
grant select, insert, update, delete on public.comments to service_role;

alter table public.profiles enable row level security;
alter table public.tickets enable row level security;
alter table public.comments enable row level security;

create policy "Authenticated users can read profiles"
  on public.profiles
  for select
  to authenticated
  using (true);

create policy "Users can update their own profile"
  on public.profiles
  for update
  to authenticated
  using ((select auth.uid()) = id)
  with check ((select auth.uid()) = id);

create policy "Requesters read their tickets and staff read all"
  on public.tickets
  for select
  to authenticated
  using (
    created_by = (select auth.uid())
    or (select private.is_staff())
  );

create policy "Users create tickets for themselves"
  on public.tickets
  for insert
  to authenticated
  with check (created_by = (select auth.uid()));

create policy "Creators and staff update tickets"
  on public.tickets
  for update
  to authenticated
  using (
    created_by = (select auth.uid())
    or (select private.is_staff())
  )
  with check (
    created_by = (select auth.uid())
    or (select private.is_staff())
  );

create policy "Users read comments on visible tickets"
  on public.comments
  for select
  to authenticated
  using (
    exists (
      select 1
      from public.tickets as ticket
      where ticket.id = ticket_id
        and (
          ticket.created_by = (select auth.uid())
          or (select private.is_staff())
        )
    )
  );

create policy "Users comment on visible tickets as themselves"
  on public.comments
  for insert
  to authenticated
  with check (
    user_id = (select auth.uid())
    and exists (
      select 1
      from public.tickets as ticket
      where ticket.id = ticket_id
        and (
          ticket.created_by = (select auth.uid())
          or (select private.is_staff())
        )
    )
  );
