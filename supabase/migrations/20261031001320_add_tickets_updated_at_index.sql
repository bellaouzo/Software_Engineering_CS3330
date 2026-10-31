-- Req 5.1 (ticket list loads in under 2 seconds). The ticket list and both
-- dashboards sort tickets by updated_at, newest first. This index lets Postgres
-- read tickets in that order instead of sorting them. It pays off when a query
-- asks for only the first rows (a limit, or paging the list); today the pages
-- load every ticket, so expect little change until the list is paged.
create index if not exists tickets_updated_at_idx
  on public.tickets (updated_at desc);
