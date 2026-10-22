-- Jarvis core schema. Applied to Supabase project pepexjsboutlqmqjyemc as migration "jarvis_core_schema".
-- Lives in its own schema so it never touches the promo app tables in `public`.
-- RLS is on with no policies: only the backend (service key) can read/write.

create extension if not exists vector with schema extensions;
create extension if not exists pg_trgm with schema extensions;

create schema if not exists jarvis;
revoke all on schema jarvis from anon, authenticated;

create or replace function jarvis.set_updated_at() returns trigger
language plpgsql set search_path = '' as $$
begin new.updated_at = now(); return new; end $$;

create table jarvis.workspaces (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique check (slug ~ '^[a-z0-9_-]{2,30}$'),
  name text not null,
  created_at timestamptz not null default now()
);

create table jarvis.contacts (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references jarvis.workspaces(id) on delete cascade,
  name text not null default '',
  platform text not null default '',
  handle text not null default '',
  phone text not null default '',
  email text not null default '',
  source text not null default '',
  status text not null default 'new' check (status in ('new','contacted','replied','won','lost','blocked')),
  notes text not null default '',
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index contacts_workspace_status_idx on jarvis.contacts (workspace_id, status);
create unique index contacts_workspace_platform_handle_uq on jarvis.contacts (workspace_id, platform, handle) where handle <> '';
create trigger contacts_updated_at before update on jarvis.contacts for each row execute function jarvis.set_updated_at();

create table jarvis.messages (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references jarvis.workspaces(id) on delete cascade,
  contact_id uuid references jarvis.contacts(id) on delete set null,
  channel text not null,
  direction text not null check (direction in ('in','out')),
  body text not null,
  status text not null default 'draft' check (status in ('draft','approved','sent','failed','received')),
  approved_at timestamptz,
  sent_at timestamptz,
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now()
);
create index messages_workspace_status_idx on jarvis.messages (workspace_id, status);
create index messages_contact_idx on jarvis.messages (contact_id);

create table jarvis.tasks (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references jarvis.workspaces(id) on delete cascade,
  title text not null,
  agent text not null default 'orchestrator',
  status text not null default 'todo' check (status in ('todo','running','needs_approval','done','failed')),
  payload jsonb not null default '{}',
  result jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index tasks_workspace_status_idx on jarvis.tasks (workspace_id, status);
create trigger tasks_updated_at before update on jarvis.tasks for each row execute function jarvis.set_updated_at();

create table jarvis.calculations (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references jarvis.workspaces(id) on delete cascade,
  title text not null,
  inputs jsonb not null default '{}',
  result jsonb not null default '{}',
  created_at timestamptz not null default now()
);
create index calculations_workspace_idx on jarvis.calculations (workspace_id, created_at desc);

create table jarvis.agent_logs (
  id bigint generated always as identity primary key,
  workspace_id uuid references jarvis.workspaces(id) on delete set null,
  agent text not null,
  action text not null,
  input jsonb,
  output jsonb,
  success boolean not null default true,
  created_at timestamptz not null default now()
);
create index agent_logs_workspace_idx on jarvis.agent_logs (workspace_id, created_at desc);

-- workspace_id null = shared memory, visible in every workspace
create table jarvis.memory (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references jarvis.workspaces(id) on delete cascade,
  kind text not null check (kind in ('preference','lesson','fact','skill')),
  content text not null,
  embedding extensions.vector(1024),
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now()
);
create index memory_workspace_kind_idx on jarvis.memory (workspace_id, kind);
create index memory_content_trgm_idx on jarvis.memory using gin (content extensions.gin_trgm_ops);

create table jarvis.improvement_proposals (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references jarvis.workspaces(id) on delete set null,
  title text not null,
  description text not null default '',
  status text not null default 'proposed' check (status in ('proposed','approved','rejected','merged')),
  pr_url text not null default '',
  created_at timestamptz not null default now()
);

alter table jarvis.workspaces enable row level security;
alter table jarvis.contacts enable row level security;
alter table jarvis.messages enable row level security;
alter table jarvis.tasks enable row level security;
alter table jarvis.calculations enable row level security;
alter table jarvis.agent_logs enable row level security;
alter table jarvis.memory enable row level security;
alter table jarvis.improvement_proposals enable row level security;

insert into jarvis.workspaces (slug, name) values
  ('ataria', 'Ataria'),
  ('kaspi', 'Kaspi'),
  ('personal', 'Личное');
