create extension if not exists pgcrypto;

create table if not exists public.clients (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    slug text not null unique,
    logo_url text,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.monitorings (
    id uuid primary key default gen_random_uuid(),
    client_id uuid not null references public.clients(id) on delete cascade,
    name text not null,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (client_id, name)
);

create table if not exists public.terms (
    id uuid primary key default gen_random_uuid(),
    monitoring_id uuid not null references public.monitorings(id) on delete cascade,
    text text not null,
    normalized_text text generated always as (lower(trim(text))) stored,
    is_primary boolean not null default false,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    unique (monitoring_id, normalized_text)
);

create table if not exists public.searches (
    id uuid primary key default gen_random_uuid(),
    monitoring_id uuid not null references public.monitorings(id) on delete cascade,
    period_hours integer not null default 24 check (period_hours between 1 and 720),
    status text not null default 'pending' check (
        status in ('pending', 'running', 'completed', 'partial', 'failed')
    ),
    started_at timestamptz not null default now(),
    finished_at timestamptz,
    result_count integer not null default 0 check (result_count >= 0),
    error_message text
);

create table if not exists public.results (
    id uuid primary key default gen_random_uuid(),
    search_id uuid not null references public.searches(id) on delete cascade,
    media_type text not null check (
        media_type in ('noticia', 'youtube', 'site', 'blog', 'rede_social')
    ),
    source text not null,
    title text not null,
    url text not null,
    published_at timestamptz,
    excerpt text,
    searched_term text not null,
    matched_term text not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_monitorings_client_id
    on public.monitorings(client_id);

create index if not exists idx_terms_monitoring_id
    on public.terms(monitoring_id);

create index if not exists idx_searches_monitoring_started_at
    on public.searches(monitoring_id, started_at desc);

create index if not exists idx_results_search_id
    on public.results(search_id);

create index if not exists idx_results_published_at
    on public.results(published_at desc);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists clients_set_updated_at on public.clients;
create trigger clients_set_updated_at
before update on public.clients
for each row execute function public.set_updated_at();

drop trigger if exists monitorings_set_updated_at on public.monitorings;
create trigger monitorings_set_updated_at
before update on public.monitorings
for each row execute function public.set_updated_at();

-- RLS is enabled now so the database does not become publicly writable by accident.
-- Policies will be added when authentication is implemented.
alter table public.clients enable row level security;
alter table public.monitorings enable row level security;
alter table public.terms enable row level security;
alter table public.searches enable row level security;
alter table public.results enable row level security;
