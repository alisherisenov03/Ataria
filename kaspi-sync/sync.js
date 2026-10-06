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
// Kaspi просит указать статус заказа; ARCHIVE нужен, чтобы видеть завершённые заказы
const STATES = ["NEW", "SIGN_REQUIRED", "PICKUP", "DELIVERY", "KASPI_DELIVERY", "ARCHIVE"];

if (!DB) { console.error("Нет DATABASE_URL"); process.exit(1); }
const pool = new pg.Pool({ connectionString: DB, ssl: DB.includes("railway.internal") ? false : { rejectUnauthorized: false } });

const headers = () => ({
  "X-Auth-Token": TOKEN,
  "Content-Type": "application/vnd.api+json",
  "User-Agent": "ataria-sync/0.2",
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
    create table if not exists kaspi_items (
      entry_id text primary key,
      order_id text not null,
      product_code text,
      product_name text,
      qty int,
      unit_price numeric,
      total_price numeric
    );
    create index if not exists kaspi_items_order_idx on kaspi_items (order_id);
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

let probed = false;
// Позиции заказа: название товара, код, количество, цена. Сохраняет в kaspi_items.
async function fetchItems(orderId) {
  try {
    const j = await api(`/orders/${orderId}/entries?include[entries]=product`);
    const inc = new Map((j.included || []).map(i => [i.id, i]));
    if (!probed) {
      probed = true;
      const e0 = (j.data || [])[0] || {};
      console.log("Форма ответа по позициям:", JSON.stringify({
        top: Object.keys(j), entryKeys: Object.keys(e0), attrKeys: Object.keys(e0.attributes || {}),
        relKeys: Object.keys(e0.relationships || {}), includedTypes: [...new Set((j.included || []).map(i => i.type))],
        includedAttrKeys: Object.keys(((j.included || [])[0] || {}).attributes || {}),
      }));
    }
    const items = (j.data || []).map(e => {
      const a = e.attributes || {};
      const pid = e.relationships?.product?.data?.id;
      const p = (pid && inc.get(pid)?.attributes) || {};
      return {
        entry_id: e.id,
        code: a.offer?.code || p.code || null,
        name: a.offer?.name || p.name || a.category?.title || "без названия",
        qty: a.quantity || 0,
        unit: a.basePrice ?? a.unitPrice ?? null,
        total: a.totalPrice ?? null,
      };
    });
    for (const it of items) {
      await pool.query(
        `insert into kaspi_items (entry_id, order_id, product_code, product_name, qty, unit_price, total_price)
         values ($1,$2,$3,$4,$5,$6,$7)
         on conflict (entry_id) do update set product_code=excluded.product_code, product_name=excluded.product_name,
           qty=excluded.qty, unit_price=excluded.unit_price, total_price=excluded.total_price`,
        [it.entry_id, orderId, it.code, it.name, it.qty, it.unit, it.total]);
    }
    return items.reduce((s, i) => s + i.qty, 0);
  } catch (e) { console.warn("Не получил позиции заказа", orderId, e.message); return null; }
}

async function syncWindow(from, to, state) {
  let page = 0, saved = 0;
  for (;;) {
    const q = `?page[number]=${page}&page[size]=100`
      + `&filter[orders][state]=${state}`
      + `&filter[orders][creationDate][$ge]=${from}&filter[orders][creationDate][$le]=${to}`;
    const j = await api("/orders" + q);
    const rows = j.data || [];
    for (const o of rows) {
      const a = o.attributes || {};
      const known = await pool.query("select qty from kaspi_orders where id=$1", [o.id]);
      const qty = known.rows[0]?.qty ?? await fetchItems(o.id);
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

// Дозаполняет товары для заказов, загруженных до появления таблицы kaspi_items
async function backfillItems() {
  const r = await pool.query(
    `select o.id from kaspi_orders o
     where not exists (select 1 from kaspi_items i where i.order_id = o.id)
     order by o.created_at desc limit 1000`);
  let n = 0;
  for (const row of r.rows) { if (await fetchItems(row.id) !== null) n++; }
  if (r.rows.length) console.log("Товары дозаполнены для заказов:", n, "из", r.rows.length);
}

async function report() {
  const today = await pool.query(
    `select state, count(*) n from kaspi_orders
     where (created_at at time zone 'Asia/Almaty')::date = (now() at time zone 'Asia/Almaty')::date
     group by state order by state`);
  console.log("Сегодня по статусам:", JSON.stringify(today.rows));
  // Открытые заказы: собран ли заказ и передан ли курьеру (по полям Kaspi). Только флаги, без данных клиентов.
  const open = await pool.query(
    `select state, status,
            raw->'attributes'->>'assembled' as assembled,
            (raw->'attributes'->'kaspiDelivery'->>'courierTransmissionDate') is not null as handed_to_courier,
            count(*) n
     from kaspi_orders where state <> 'ARCHIVE' group by 1,2,3,4 order by 1,2,3,4`);
  console.log("Открытые заказы:", JSON.stringify(open.rows));
  const keys = await pool.query(
    `select (select array_agg(k) from jsonb_object_keys(raw->'attributes') k) as attr_keys,
            (select array_agg(k) from jsonb_object_keys(coalesce(raw->'attributes'->'kaspiDelivery','{}'::jsonb)) k) as delivery_keys
     from kaspi_orders where state <> 'ARCHIVE' order by created_at desc limit 1`);
  console.log("Поля заказа:", JSON.stringify(keys.rows[0] || {}));
  const prod = await pool.query(
    `select i.product_name, i.product_code, sum(i.qty) units, sum(i.total_price) revenue,
            count(distinct i.order_id) orders, round(sum(i.total_price)/nullif(sum(i.qty),0)) avg_price
     from kaspi_items i join kaspi_orders o on o.id = i.order_id
     where o.state not in ('CANCELLED','CANCELLING')
     group by 1,2 order by revenue desc nulls last limit 60`);
  console.log("Товары за 60 дней:", JSON.stringify(prod.rows));
  const days = await pool.query(
    "select to_char(day,'YYYY-MM-DD') d, orders, units, revenue from daily_sales order by day desc limit 10");
  console.log("Продажи по дням (заказы/штуки/выручка):", JSON.stringify(days.rows));
}

let running = false;
async function run() {
  if (running) return;
  running = true;
  try {
    const row = await pool.query("select value from sync_state where key='last_to'");
    const now = Date.now();
    let from = row.rows[0] ? Number(row.rows[0].value) - DAY : now - BACKFILL_DAYS * DAY;
    let total = 0;
    while (from < now) {
      const to = Math.min(from + WINDOW, now);
      for (const state of STATES) {
        try {
          const n = await syncWindow(from, to, state);
          total += n;
          console.log(`${new Date(from).toISOString().slice(0, 10)}..${new Date(to).toISOString().slice(0, 10)} ${state}: ${n}`);
        } catch (e) { console.error(`Ошибка ${state}:`, e.message); }
      }
      from = to;
    }
    await pool.query(
      "insert into sync_state (key, value) values ('last_to',$1) on conflict (key) do update set value=excluded.value",
      [String(now)]);
    console.log(new Date().toISOString(), "заказов обновлено:", total);
    await backfillItems();
    await report();
  } finally { running = false; }
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
