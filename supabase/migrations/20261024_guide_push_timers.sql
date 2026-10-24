-- Web Push timers for the ATARIA guide site. Service-role only (RLS on, no policies).
create table if not exists public.guide_push_config (key text primary key, value text not null);
create table if not exists public.guide_timers (
  id uuid primary key default gen_random_uuid(),
  endpoint text not null,
  sub jsonb not null,
  fire_at timestamptz not null,
  title text not null,
  body text not null,
  url text not null default '/',
  sent boolean not null default false,
  error text,
  created_at timestamptz not null default now()
);
create index if not exists guide_timers_due_idx on public.guide_timers (fire_at) where not sent;
create index if not exists guide_timers_endpoint_idx on public.guide_timers (endpoint) where not sent;
alter table public.guide_push_config enable row level security;
alter table public.guide_timers enable row level security;

create or replace function public.guide_push_tick() returns void
language plpgsql security definer set search_path = public, extensions as $$
begin
  if exists (select 1 from public.guide_timers where not sent and fire_at <= now()) then
    perform net.http_post(
      url := 'https://pepexjsboutlqmqjyemc.supabase.co/functions/v1/guide-push?action=dispatch',
      headers := '{"Content-Type":"application/json"}'::jsonb,
      body := '{}'::jsonb,
      timeout_milliseconds := 20000);
  end if;
  delete from public.guide_timers where created_at < now() - interval '1 day';
end $$;
revoke all on function public.guide_push_tick() from public, anon, authenticated;

-- VAPID keys are inserted separately (guide_push_config: vapid_public, vapid_private).
-- select cron.schedule('guide-push-tick', '10 seconds', 'select public.guide_push_tick()');
