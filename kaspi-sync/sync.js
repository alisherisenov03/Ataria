// Забирает заказы Kaspi Магазина и складывает их в Postgres (Railway).
// Переменные окружения: KASPI_TOKEN (обязательно), DATABASE_URL (даёт Railway),
// SYNC_MINUTES (по умолчанию 10), BACKFILL_DAYS (по умолчанию 60).
import pg from "pg";

const TOKEN = process.env.KASPI_TOKEN;
const DB = process.env.DATABASE_URL;
const EVERY_MIN = Number(process.env.SYNC_MINUTES || 10);
const BACKFILL_DAYS = Number(process.env.BACKFILL_DAYS || 60);
const BASE = "https://kaspi.kz/shop/api/v2";
const DAY = 864e5;
const WINDOW = 14 * DAY; // Kaspi отдаёт заказы окнами не больше 14 дней

if (!DB) { console.error("Нет DATABASE_URL"); process.exit(1); }
const pool = new pg.Pool({ connectionString: DB, ssl: DB.includes("railway.internal") ? false : { rejectUnauthorized: false } });

const headers = () => ({
  "X-Auth-Token": TOKEN,
  "Content-Type": "application/vnd.api+json",
  "User-Agent": "ataria-sync/0.1",
});

async function api(path) {
  const res = await fetch(BASE + path, { headers: headers() });
  if (!res.ok) throw new Error(`Kaspi ${res.status} на ${path.split("?")[0]}`);
  return res.json();
}

async function init() {
  await pool.query(`
    create table if not exists kaspi_orders (
      id text primary key,
      code text,
      state text,
      status text,
      created_at timestamptz,
      total_price numeric,
      payment_mode text,
      qty int,
      raw jsonb not null,
      synced_at timestamptz default now()
    );
    create index if not exists kaspi_orders_created_idx on kaspi_orders (created_at);
    create table if not exists sync_state (key text primary key, value text);
    create or replace view daily_sales as
      select (created_at at time zone 'Asia/Almaty')::date as day,
             count(*) as orders,
             coalesce(sum(qty), 0) as units,
             coalesce(sum(total_price), 0) as revenue
      from kaspi_orders
      where state not in ('CANCELLED', 'CANCELLING')
      group by 1 order by 1;
  `);
}

async function qtyOf(orderId) {
  try {
    const j = await api(`/orders/${orderId}/entries`);
    return (j.data || []).reduce((s, e) => s + (e.attributes?.quantity || 0), 0);
  } catch (e) { console.warn("Не получил позиции заказа", orderId, e.message); return null; }
}

async function syncWindow(from, to) {
  let page = 0, saved = 0;
  for (;;) {
    const q = `?page[number]=${page}&page[size]=100`
      + `&filter[orders][creationDate][$ge]=${from}&filter[orders][creationDate][$le]=${to}`;
    const j = await api("/orders" + q);
    const rows = j.data || [];
    for (const o of rows) {
      const a = o.attributes || {};
      const known = await pool.query("select qty from kaspi_orders where id=$1", [o.id]);
      const qty = known.rows[0]?.qty ?? await qtyOf(o.id);
      await pool.query(
        `insert into kaspi_orders (id, code, state, status, created_at, total_price, payment_mode, qty, raw)
         values ($1,$2,$3,$4,to_timestamp($5/1000.0),$6,$7,$8,$9)
         on conflict (id) do update set state=excluded.state, status=excluded.status,
           total_price=excluded.total_price, qty=coalesce(excluded.qty, kaspi_orders.qty),
           raw=excluded.raw, synced_at=now()`,
        [o.id, a.code, a.state, a.status, a.creationDate, a.totalPrice, a.paymentMode, qty, o]);
      saved++;
    }
    const pages = j.meta?.pageCount ?? 1;
    page++;
    if (page >= pages || rows.length === 0) break;
  }
  return saved;
}

async function run() {
  const row = await pool.query("select value from sync_state where key='last_to'");
  const now = Date.now();
  let from = row.rows[0] ? Number(row.rows[0].value) - DAY : now - BACKFILL_DAYS * DAY;
  let total = 0;
  while (from < now) {
    const to = Math.min(from + WINDOW, now);
    total += await syncWindow(from, to);
    from = to;
  }
  await pool.query(
    "insert into sync_state (key, value) values ('last_to',$1) on conflict (key) do update set value=excluded.value",
    [String(now)]);
  console.log(new Date().toISOString(), "заказов обновлено:", total);
}

async function main() {
  await init();
  if (!TOKEN) {
    console.log("KASPI_TOKEN не задан. База готова. После добавления переменной Railway перезапустит сервис.");
    setInterval(() => {}, 60 * 60 * 1000);
    return;
  }
  const tick = () => run().catch(e => console.error("Ошибка синхронизации:", e.message));
  await tick();
  setInterval(tick, EVERY_MIN * 60 * 1000);
}
main();
