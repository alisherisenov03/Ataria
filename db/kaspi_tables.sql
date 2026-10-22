-- Kaspi orders storage in the unified DB (mirrors the kaspi-sync Railway Postgres tables).
-- Applied as migration "jarvis_kaspi_tables". Data is copied in separately.
create table jarvis.kaspi_orders (
  id text primary key, code text, state text, status text, created_at timestamptz,
  total_price numeric, payment_mode text, qty int, raw jsonb not null, synced_at timestamptz default now()
);
create index kaspi_orders_created_idx on jarvis.kaspi_orders (created_at);
create table jarvis.kaspi_items (
  entry_id text primary key, order_id text not null, product_code text, product_name text,
  qty int, unit_price numeric, total_price numeric
);
create index kaspi_items_order_idx on jarvis.kaspi_items (order_id);
create table jarvis.kaspi_product_owner (code text primary key, owner text not null);
create view jarvis.kaspi_daily_sales with (security_invoker = true) as
  select (created_at at time zone 'Asia/Almaty')::date as day, count(*) as orders,
         coalesce(sum(qty), 0) as units, coalesce(sum(total_price), 0) as revenue
  from jarvis.kaspi_orders
  where state not in ('CANCELLED', 'CANCELLING')
    and coalesce(status,'') not in ('CANCELLED','CANCELLING','RETURNED') and total_price >= 1000
  group by 1 order by 1;
alter table jarvis.kaspi_orders enable row level security;
alter table jarvis.kaspi_items enable row level security;
alter table jarvis.kaspi_product_owner enable row level security;
grant all on jarvis.kaspi_orders, jarvis.kaspi_items, jarvis.kaspi_product_owner to service_role;
grant select on jarvis.kaspi_daily_sales to service_role;
