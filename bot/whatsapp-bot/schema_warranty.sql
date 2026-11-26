-- Warranty registrations from the QR card in the box (WhatsApp bot).
create table if not exists public.warranty_registrations (
  id bigint generated always as identity primary key,
  phone text not null,
  kaspi_order text not null,
  product text not null default '',
  has_photo boolean not null default false,
  status text not null default 'rules_sent' check (status in ('rules_sent', 'registered')),
  rules_accepted_at timestamptz,
  warranty_until date,
  created_at timestamptz not null default now(),
  unique (phone, kaspi_order)
);
alter table public.warranty_registrations enable row level security;
