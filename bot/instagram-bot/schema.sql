-- Instagram DM bot: conversations, UGC creator pipeline, token storage.
-- Orders and handoffs reuse wa_orders / wa_handoffs with phone = 'ig:<igsid>'.

create table public.ugc_leads (
  handle text primary key,                  -- instagram username, lowercase, no @
  city text not null default '',
  kind text not null default '',            -- мама, UGC, лайфстайл...
  followers text not null default '',
  offer text not null default 'A' check (offer in ('A', 'C')),  -- A barter; C barter + promo code
  status text not null default 'новый' check (status in
    ('новый', 'написали', 'думает', 'согласна', 'подушка отправлена', 'ролик сдан', 'закрыто', 'отказ')),
  igsid text unique,                        -- set when the conversation starts
  full_name text not null default '',
  ship_city text not null default '',
  ship_address text not null default '',
  ship_phone text not null default '',
  scenario text not null default '',
  note text not null default '',
  updated_at timestamptz not null default now()
);

create table public.ig_threads (
  igsid text primary key,                   -- the other person's Instagram-scoped id
  username text not null default '',
  kind text not null check (kind in ('creator', 'customer')),
  bot_paused boolean not null default false, -- owner took over the chat
  created_at timestamptz not null default now()
);

create table public.ig_messages (
  id bigint generated always as identity primary key,
  ig_mid text unique,
  igsid text not null references public.ig_threads (igsid),
  role text not null check (role in ('user', 'assistant')),
  content jsonb not null,
  created_at timestamptz not null default now()
);
create index ig_messages_thread on public.ig_messages (igsid, id);

create table public.ig_config (
  key text primary key,
  value text not null,
  updated_at timestamptz not null default now()
);

alter table public.ugc_leads enable row level security;
alter table public.ig_threads enable row level security;
alter table public.ig_messages enable row level security;
alter table public.ig_config enable row level security;

-- ids of every message the bot sent (a reply can go out as several messages):
-- their echoes must not be taken for the owner typing by hand
create table public.ig_sent (
  mid text primary key,
  created_at timestamptz not null default now()
);
alter table public.ig_sent enable row level security;
