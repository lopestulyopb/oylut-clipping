create table if not exists public.schedules (
  id uuid primary key default gen_random_uuid(),
  monitoring_id uuid not null references public.monitorings(id) on delete cascade,
  frequency text not null check (frequency in ('daily','weekly')),
  weekday smallint check (weekday between 0 and 6),
  run_time time not null,
  start_date date not null,
  end_date date,
  period_hours integer not null default 24,
  timezone text not null default 'America/Fortaleza',
  is_active boolean not null default true,
  last_run_at timestamptz,
  next_run_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists schedules_monitoring_idx on public.schedules(monitoring_id);
create index if not exists schedules_due_idx on public.schedules(is_active,next_run_at);

alter table public.results add column if not exists sentiment text check (sentiment in ('positive','neutral','negative'));
alter table public.clipping_items add column if not exists sentiment text check (sentiment in ('positive','neutral','negative'));
