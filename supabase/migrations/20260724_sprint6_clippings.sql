create extension if not exists pgcrypto;

create table if not exists public.clippings (
    id uuid primary key default gen_random_uuid(),
    monitoring_id uuid null references public.monitorings(id) on delete set null,
    search_id uuid null references public.searches(id) on delete set null,
    title text not null,
    client_name text null,
    monitoring_name text null,
    item_count integer not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.clipping_items (
    id uuid primary key default gen_random_uuid(),
    clipping_id uuid not null references public.clippings(id) on delete cascade,
    position integer not null default 0,
    source text not null,
    title text not null,
    url text not null,
    matched_term text null,
    published_at timestamptz null,
    excerpt text null,
    created_at timestamptz not null default now()
);

create index if not exists clippings_created_at_idx on public.clippings(created_at desc);
create index if not exists clipping_items_clipping_id_idx on public.clipping_items(clipping_id, position);
