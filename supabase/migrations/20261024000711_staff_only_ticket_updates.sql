-- F-001 (Req 2.3.1, 4.1): "Creators and staff update tickets" from
-- 20260926005657_create_ticketing_tables.sql let a requester update their own
-- ticket, including its status. Replace it so only staff can update tickets.
-- Requesters still create and read their own tickets through the insert and
-- select policies, which are unchanged.
drop policy if exists "Creators and staff update tickets" on public.tickets;

create policy "Staff update tickets"
  on public.tickets
  for update
  to authenticated
  using ((select private.is_staff()))
  with check ((select private.is_staff()));
