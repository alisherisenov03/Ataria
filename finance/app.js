'use strict';
// «Финансы» — личный и бизнес-учёт. Данные: Supabase (таблицы public.fin_*), общие со всеми чатами Claude.
const SUPABASE_URL = 'https://pepexjsboutlqmqjyemc.supabase.co';
const SUPABASE_KEY = 'sb_publishable_dbx9iZ1VPXYGZfYZip8oRw_1JUGpb9V'; // публичный ключ; доступ закрыт политиками RLS
const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY, {
  auth: { persistSession: true, autoRefreshToken: true, storageKey: 'fin-auth' },
});

const APP_VERSION = '4'; // bump together with version.json on every release

const S = {
  session: null, owner: false, tab: 'home', month: ym(new Date()),
  accounts: [], projects: [], categories: [], budgets: [], txs: [], kaspi: [],
  filterProject: null, loading: false, company: null,
  draft: { text: '', files: [] }, sending: false, mode: (() => { try { return localStorage.getItem('fin-mode') || 'personal'; } catch (_) { return 'personal'; } })(), details: false,
};

/* ---------- helpers ---------- */
function ym(d) { return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0'); }
function today() { const d = new Date(); return ym(d) + '-' + String(d.getDate()).padStart(2, '0'); }
function monthRange(m) {
  const [y, mo] = m.split('-').map(Number);
  const last = new Date(y, mo, 0).getDate();
  return [m + '-01', m + '-' + String(last).padStart(2, '0')];
}
function shiftMonth(m, k) { const [y, mo] = m.split('-').map(Number); return ym(new Date(y, mo - 1 + k, 1)); }
const MONTHS = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];
function monthName(m) { const [y, mo] = m.split('-').map(Number); return MONTHS[mo - 1] + ' ' + y; }
const nf = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 });
function money(v, sign) {
  const n = Math.round(Number(v) || 0);
  const s = nf.format(Math.abs(n)) + ' ₸';
  if (sign && n > 0) return '+' + s;
  return n < 0 ? '−' + s : s;
}
function esc(s) { return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
function dayLabel(d) {
  if (d === today()) return 'Сегодня';
  const y = new Date(); y.setDate(y.getDate() - 1);
  if (d === ym(y) + '-' + String(y.getDate()).padStart(2, '0')) return 'Вчера';
  const [yy, mm, dd] = d.split('-').map(Number);
  return dd + ' ' + ['янв','фев','мар','апр','мая','июн','июл','авг','сен','окт','ноя','дек'][mm - 1] + (yy !== new Date().getFullYear() ? ' ' + yy : '');
}
const byId = (arr, id) => arr.find(x => x.id === id);
const $ = sel => document.querySelector(sel);
function toast(msg) {
  const t = document.createElement('div'); t.className = 'toast'; t.textContent = msg;
  document.body.appendChild(t); setTimeout(() => t.remove(), 2200);
}
function parseAmount(s) { return Number(String(s).replace(/\s/g, '').replace(',', '.')); }

/* ---------- data ---------- */
async function loadRefs() {
  const [a, p, c, b] = await Promise.all([
    sb.from('fin_account_balances').select('*').order('sort'),
    sb.from('fin_projects').select('*').order('sort'),
    sb.from('fin_categories').select('*').order('sort'),
    sb.from('fin_budgets').select('*'),
  ]);
  for (const r of [a, p, c, b]) if (r.error) throw r.error;
  S.accounts = a.data; S.projects = p.data; S.categories = c.data; S.budgets = b.data;
}
async function loadMonth() {
  const [from, to] = monthRange(S.month);
  const { data, error } = await sb.from('fin_transactions').select('*')
    .gte('occurred_on', from).lte('occurred_on', to)
    .order('occurred_on', { ascending: false }).order('created_at', { ascending: false });
  if (error) throw error;
  S.txs = data;
}
async function loadKaspi() {
  const from = shiftMonth(ym(new Date()), -11) + '-01';
  const { data, error } = await sb.rpc('fin_kaspi_monthly', { p_from: from });
  S.kaspi = error ? [] : data;
}
async function loadCompany() {
  const { data, error } = await sb.rpc('fin_company');
  S.company = error ? null : data;
}
async function reloadAll() {
  S.loading = true;
  try { await Promise.all([loadRefs(), loadMonth(), loadKaspi(), loadCompany()]); }
  catch (e) { toast('Ошибка загрузки: ' + e.message); }
  S.loading = false; render();
}

/* ---------- calculations ---------- */
function monthTotals(txs) {
  let inc = 0, exp = 0;
  for (const t of txs) { if (t.type === 'income') inc += +t.amount; else if (t.type === 'expense') exp += +t.amount; }
  return { inc, exp };
}
function kaspiFor(month, slug) {
  return S.kaspi.filter(k => k.month === month && (!slug || k.project_slug === slug))
    .reduce((s, k) => ({ revenue: s.revenue + +k.revenue, fee: s.fee + +k.kaspi_fee, cogs: s.cogs + +k.cogs, units: s.units + +k.units, orders: s.orders + +k.orders }),
      { revenue: 0, fee: 0, cogs: 0, units: 0, orders: 0 });
}
function projectStats(p) {
  const txs = S.txs.filter(t => t.project_id === p.id);
  const { inc, exp } = monthTotals(txs);
  const k = p.kind === 'business' ? kaspiFor(S.month, p.slug) : { revenue: 0, fee: 0, cogs: 0, units: 0 };
  // Закуп товара — это деньги в запас, а не расход месяца: в прибыль идёт себестоимость проданного (cogs).
  const purchase = S.categories.find(c => c.type === 'expense' && c.name === 'Закуп товара')?.id;
  const opex = txs.filter(t => t.type === 'expense' && t.category_id !== purchase).reduce((s, t) => s + +t.amount, 0);
  const profit = inc + k.revenue - k.fee - k.cogs - opex;
  return { inc, exp, k, profit };
}
function budgetUsage(b) {
  const spent = S.txs.filter(t => t.type === 'expense'
    && (!b.project_id || t.project_id === b.project_id)
    && (!b.category_id || t.category_id === b.category_id)).reduce((s, t) => s + +t.amount, 0);
  return { spent, pct: spent / b.monthly_limit };
}
function budgetName(b) {
  const p = byId(S.projects, b.project_id), c = byId(S.categories, b.category_id);
  return [p?.name, c?.name].filter(Boolean).join(' · ') || 'Все расходы';
}

/* ---------- icons ---------- */
const I = {
  home: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z"/></svg>',
  list: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M8 6h13M8 12h13M8 18h13M3.5 6h.01M3.5 12h.01M3.5 18h.01"/></svg>',
  plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>',
  card: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="2.5" y="5" width="19" height="14" rx="2.5"/><path d="M2.5 10h19M6 15h4"/></svg>',
  folder: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M3 6.5A1.5 1.5 0 0 1 4.5 5H9l2 2.5h8.5A1.5 1.5 0 0 1 21 9v9.5a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 18.5z"/></svg>',
};
const ACC_ICON = { card: '💳', business: '🏪', deposit: '🏦', cash: '💵', other: '👛' };

/* ---------- views ---------- */
function monthNav() {
  return `<div class="monthnav"><button data-act="prev" aria-label="Предыдущий месяц">‹</button><span>${monthName(S.month)}</span><button data-act="next" aria-label="Следующий месяц">›</button></div>`;
}

// Business money vs Kaspi: sales from the order sync against the cabinet's revenue, plus money still on its way from Kaspi
function kaspiCheck(c) {
  const p = c.pnl_month;
  const fromOrders = S.kaspi.filter(k => k.month === S.month).reduce((s, k) => s + +k.revenue, 0);
  const inCabinet = p && p.month === S.month ? +p.to_date?.['Выручка'] || 0 : null;
  if (!fromOrders && inCabinet == null && !c.kaspi_intransit) return '';
  const diff = inCabinet != null ? fromOrders - inCabinet : 0;
  const ok = inCabinet == null || Math.abs(diff) <= Math.max(1000, fromOrders * 0.01);
  return `<div class="muted small" style="margin-top:10px">Сверка с Kaspi</div>
    <div class="row between small" style="margin-top:3px"><span>Продажи по заказам Kaspi</span><span class="num">${money(fromOrders)}</span></div>
    ${inCabinet != null ? `<div class="row between small"><span>Выручка в кабинете</span><span class="num">${money(inCabinet)}</span></div>
    <div class="row between small ${ok ? 'pos' : 'warn'}"><span>${ok ? '✓ сходится' : 'Расхождение'}</span><span class="num">${ok ? '' : money(diff, true)}</span></div>` : ''}
    ${c.kaspi_intransit ? `<div class="row between small"><span>В пути от Kaspi (${c.kaspi_intransit_orders} зак.)</span><span class="num">${money(c.kaspi_intransit)}</span></div>` : ''}`;
}

function companyCard() {
  const c = S.company;
  if (!c) return '';
  const p = c.pnl_month;
  const up = (c.upcoming || []).slice(0, 3);
  const pending = S.txs.filter(t => t.cabinet_status === 'pending').length;
  return `<h2>Компания (кабинет Kaspi)</h2>
    <div class="card">
      <div class="row between"><span>Счёт компании</span><b class="num">${money(c.cash)}</b></div>
      ${c.reserve ? `<div class="row between muted small"><span>из них резерв</span><span class="num">${money(c.reserve)}</span></div>` : ''}
      <div class="row between" style="margin-top:6px"><span>Компания должна вам</span><b class="num warn">${money(c.owner_debt)}</b></div>
      ${p ? `<div class="row between" style="margin-top:6px"><span>Чистая прибыль, ${esc(MONTHS[+p.month.slice(5) - 1].toLowerCase())}</span><b class="num ${p.net_to_date >= 0 ? 'pos' : 'neg'}">${money(p.net_to_date, true)}</b></div>
      <div class="row between muted small"><span>прогноз на месяц</span><span class="num">${money(p.net_forecast, true)}</span></div>` : ''}
      ${up.length ? `<div class="muted small" style="margin-top:10px">Ближайшие платежи</div>${up.map(x => `<div class="row between small" style="margin-top:3px"><span class="ell">${dayLabel(x.date)} · ${esc(x.name)}</span><span class="num">${money(x.amount)}</span></div>`).join('')}` : ''}
      ${kaspiCheck(c)}
      <div class="muted small" style="margin-top:8px">Данные кабинета на ${esc(c.asof || '')}.${pending ? ` Ждут передачи в кабинет: ${pending}.` : ''}</div>
    </div>`;
}

function homeDetails() {
  const active = S.accounts.filter(a => !a.archived);
  const total = active.reduce((s, a) => s + +a.balance, 0);
  const m = monthTotals(S.txs);
  const k = kaspiFor(S.month);
  const inc = m.inc, exp = m.exp;  // only this ledger; company revenue lives in the cabinet block
  const personal = S.projects.find(p => p.slug === 'personal');
  const personalExp = S.txs.filter(t => t.type === 'expense' && t.project_id === personal?.id).reduce((s, t) => s + +t.amount, 0);
  const bizExp = exp - personalExp;
  const pnl = S.company?.pnl_month?.month === S.month ? S.company.pnl_month : null;
  const bizProfit = pnl ? pnl.net_to_date : S.projects.filter(p => p.kind === 'business').reduce((s, p) => s + projectStats(p).profit, 0);

  const cats = {};
  for (const t of S.txs) if (t.type === 'expense') cats[t.category_id || '-'] = (cats[t.category_id || '-'] || 0) + +t.amount;
  const topCats = Object.entries(cats).sort((a, b) => b[1] - a[1]).slice(0, 6);
  const maxCat = topCats[0]?.[1] || 1;

  const alerts = S.budgets.map(b => ({ b, ...budgetUsage(b) })).filter(x => x.pct >= 0.8).sort((a, b) => b.pct - a.pct);

  return `<div>
    <div class="card">
      <div class="muted small">Всего на счетах</div>
      <div class="big num">${money(total)}</div>
      <div class="chips" style="margin-top:8px">${active.map(a => `<span class="chip">${ACC_ICON[a.kind] || ''} ${esc(a.name)} <b class="num">${money(a.balance)}</b></span>`).join('')}</div>
    </div>
    <div class="grid3">
      <div class="card"><div class="muted small">Доходы</div><div class="v num pos">${money(inc)}</div></div>
      <div class="card"><div class="muted small">Расходы</div><div class="v num neg">${money(exp)}</div></div>
      <div class="card"><div class="muted small">Итог</div><div class="v num ${inc - exp >= 0 ? 'pos' : 'neg'}">${money(inc - exp, true)}</div></div>
    </div>
    <div class="grid3" style="margin-top:8px">
      <div class="card"><div class="muted small">Личное</div><div class="v num">${money(personalExp)}</div></div>
      <div class="card"><div class="muted small">Бизнес расх.</div><div class="v num">${money(bizExp)}</div></div>
      <div class="card"><div class="muted small">Прибыль бизн.${pnl ? '' : '*'}</div><div class="v num ${bizProfit >= 0 ? 'pos' : 'neg'}">${money(bizProfit, true)}</div></div>
    </div>

    ${alerts.length ? `<h2>Бюджеты</h2><div class="card list">${alerts.map(x => `
      <div class="item" data-go="projects"><div class="grow"><div class="row between"><span class="ell">${esc(budgetName(x.b))}</span>
      <span class="num small ${x.pct >= 1 ? 'neg' : 'warn'}">${money(x.spent)} / ${money(x.b.monthly_limit)}</span></div>
      <div class="bar"><i style="width:${Math.min(100, x.pct * 100)}%;background:var(${x.pct >= 1 ? '--neg' : '--warn'})"></i></div></div></div>`).join('')}</div>` : ''}

    ${companyCard()}

    <h2>Kaspi за месяц</h2>
    <div class="card">
      ${k.revenue ? `
      <div class="row between"><span>Продажи (${k.orders} заказов)</span><b class="num">${money(k.revenue)}</b></div>
      <div class="row between muted small" style="margin-top:4px"><span>Комиссия Kaspi ≈</span><span class="num">${money(-k.fee)}</span></div>
      <div class="row between muted small"><span>Себестоимость ≈</span><span class="num">${money(-k.cogs)}</span></div>
      <div class="row between" style="margin-top:6px"><span>Валовая прибыль ≈</span><b class="num pos">${money(k.revenue - k.fee - k.cogs)}</b></div>
      <div class="muted small" style="margin-top:6px">Считается автоматически из заказов Kaspi (без отмен и возвратов, без товаров партнёра).</div>`
      : '<div class="muted">Нет продаж Kaspi за этот месяц.</div>'}
    </div>

    <h2>Куда ушли деньги</h2>
    <div class="card">${topCats.length ? topCats.map(([cid, v]) => {
      const c = byId(S.categories, cid);
      return `<div style="margin:6px 0 10px"><div class="row between"><span>${c ? c.icon + ' ' + esc(c.name) : 'Без категории'}</span><span class="num">${money(v)}</span></div>
        <div class="bar"><i style="width:${(v / maxCat) * 100}%;background:var(--accent)"></i></div></div>`;
    }).join('') : '<div class="muted">Расходов за месяц пока нет.</div>'}</div>

    <div class="muted small" style="margin:6px 4px">${pnl ? 'Прибыль бизнеса — чистая прибыль с начала месяца из кабинета Kaspi.' : '* Прибыль бизнеса = продажи Kaspi − комиссия − себестоимость проданного + прочие доходы − расходы бизнес-проектов (кроме закупа товара: он учтён через себестоимость).'}</div>
  </div>`;
}

/* ---------- visual home ---------- */
// categorical slots (validated reference palette); text never wears these colors
const SERIES = ['var(--s1)', 'var(--s2)', 'var(--s3)', 'var(--s4)', 'var(--s5)', 'var(--s6)'];
function compact(v) {
  const n = Math.abs(Math.round(+v || 0)), sign = v < 0 ? '−' : '';
  if (n >= 1e6) return sign + (n / 1e6).toLocaleString('ru-RU', { maximumFractionDigits: n >= 1e7 ? 0 : 1 }) + ' млн ₸';
  if (n >= 1e3) return sign + Math.round(n / 1e3).toLocaleString('ru-RU') + ' тыс ₸';
  return sign + n + ' ₸';
}
// one whole split into <= 6 parts: tall segmented bar + legend, tap a block for its amount
function segBar(parts, total) {
  parts = parts.filter(p => p.v > 0);
  if (!parts.length) return '';
  total = total || parts.reduce((s, p) => s + p.v, 0);
  return `<div class="seg-bar" role="img" aria-label="${esc(parts.map(p => `${p.name}: ${compact(p.v)}`).join(', '))}">${parts.map((p, i) => {
    const pct = p.v / total * 100;
    const ink = p.color ? (p.color === 'var(--other)' ? '#0b0b0b' : '#fff') : ['#fff', '#fff', '#0b0b0b', '#0b0b0b', '#0b0b0b', '#fff'][i];
    return `<i style="flex:${p.v};background:${p.color || SERIES[i]};color:${ink}" data-tip="${esc(p.name)} · ${compact(p.v)} · ${Math.round(pct)}%">${pct >= 12 ? Math.round(pct) + '%' : ''}</i>`;
  }).join('')}</div>
  <div class="legend">${parts.map((p, i) => `<span><i style="background:${p.color || SERIES[i]}"></i>${p.icon ? p.icon + ' ' : ''}${esc(p.name)}</span>`).join('')}</div>`;
}
// ranked horizontal bars, one hue
function rankBars(rows) {
  const max = Math.max(...rows.map(r => r.v), 1);
  return rows.map(r => `<div class="rb" data-tip="${esc(r.name)} · ${compact(r.v)}"><div class="row between small"><span>${r.icon || ''} ${esc(r.name)}</span><span class="muted">${compact(r.v)}</span></div>
    <div class="rb-track"><i style="width:${Math.max(2, r.v / max * 100)}%"></i></div></div>`).join('');
}
// columns over time, one series, the current one in the accent
function columns(items, label) {
  const max = Math.max(...items.map(x => x.v), 1);
  return `<div class="cols" role="img" aria-label="${esc(label)}">${items.map(x => `<div class="col" data-tip="${esc(x.tip)}"><i class="${x.on ? 'on' : ''}" style="height:${x.v > 0 ? Math.max(3, x.v / max * 100) : 0}%"></i><span>${esc(x.label)}</span></div>`).join('')}</div>`;
}
function meter(label, used, limit) {
  const pct = limit > 0 ? used / limit : 0;
  const tone = pct >= 1 ? 'neg' : pct >= 0.8 ? 'warn' : 'ok';
  return `<div class="meter ${tone}" data-tip="${esc(label)}: ${compact(used)} из ${compact(limit)}"><div class="row between small"><span>${esc(label)}</span><span class="muted">${Math.round(pct * 100)}%</span></div><div class="m-track"><i style="width:${Math.min(100, pct * 100)}%"></i></div></div>`;
}

function personalVisual() {
  const accs = S.accounts.filter(a => !a.archived && a.balance_source !== 'cabinet');
  const total = accs.reduce((s, a) => s + Math.max(0, +a.balance), 0);
  const mine = S.txs.filter(t => !t.company);
  const spent = mine.filter(t => t.type === 'expense').reduce((s, t) => s + +t.amount, 0);
  const got = mine.filter(t => t.type === 'income').reduce((s, t) => s + +t.amount, 0);

  const cats = {};
  for (const t of mine) if (t.type === 'expense') cats[t.category_id || '-'] = (cats[t.category_id || '-'] || 0) + +t.amount;
  let parts = Object.entries(cats).sort((a, b) => b[1] - a[1]).map(([id, v]) => { const c = byId(S.categories, id); return { name: c?.name || 'Без категории', icon: c?.icon, v }; });
  if (parts.length > 6) parts = [...parts.slice(0, 5), { name: 'Остальное', v: parts.slice(5).reduce((s, p) => s + p.v, 0), color: 'var(--other)' }];

  const [y, mo] = S.month.split('-').map(Number), days = new Date(y, mo, 0).getDate();
  const byDay = Array(days).fill(0);
  for (const t of mine) if (t.type === 'expense') byDay[+t.occurred_on.slice(8) - 1] += +t.amount;
  const todayN = S.month === ym(new Date()) ? new Date().getDate() : 0;

  const budgets = S.budgets.map(b => ({ b, ...budgetUsage(b) })).sort((a, b) => b.pct - a.pct).slice(0, 3);
  const mood = !spent ? '🌱' : got && spent > got ? '🔥' : '🙂';

  return `
    <div class="card hero">
      <div class="muted small">Ваши деньги сейчас</div>
      <div class="hero-v">${compact(total)}</div>
      ${segBar(accs.map(a => ({ name: a.name, icon: ACC_ICON[a.kind], v: Math.max(0, +a.balance) })), total)}
    </div>
    <div class="grid2">
      <div class="card tile"><div class="t-ico">💸</div><div class="muted small">Потрачено</div><div class="t-v">${compact(spent)}</div></div>
      <div class="card tile"><div class="t-ico">${mood}</div><div class="muted small">Пришло</div><div class="t-v">${compact(got)}</div></div>
    </div>
    <div class="card"><b>Куда уходят деньги</b>${parts.length ? segBar(parts) : '<div class="muted small" style="margin-top:8px">В этом месяце трат пока нет.</div>'}</div>
    <div class="card"><b>Траты по дням</b>${columns(byDay.map((v, i) => ({ v, label: (i + 1) % 5 === 0 || i === 0 ? String(i + 1) : '', on: i + 1 === todayN, tip: `${i + 1} ${['янв','фев','мар','апр','мая','июн','июл','авг','сен','окт','ноя','дек'][mo - 1]} · ${compact(v)}` })), 'Траты по дням месяца')}</div>
    ${budgets.length ? `<div class="card"><b>Лимиты</b>${budgets.map(x => meter(budgetName(x.b), x.spent, x.b.monthly_limit)).join('')}</div>` : ''}`;
}

function businessVisual() {
  const c = S.company;
  const pnl = c?.pnl_month?.month === S.month ? c.pnl_month : null;
  const ks = S.kaspi.filter(k => k.month === S.month);
  const name = { combines: ['Комбайны', '🍳'], pillows: ['Подушки', '🛏'], choppers: ['Измельчители', '🔪'], business: ['Другое', '📦'] };
  const products = ks.map(k => ({ name: name[k.project_slug]?.[0] || k.project_slug, icon: name[k.project_slug]?.[1], v: +k.revenue })).sort((a, b) => b.v - a.v);

  let split = '';
  if (pnl) {
    const td = pnl.to_date || {}, rev = +td['Выручка'] || 0;
    const g = (keys) => keys.reduce((s, k) => s + Math.max(0, -(+td[k] || 0)), 0);
    const parts = [
      { name: 'Товар и карго', v: g(['Товар: закуп и карго']) },
      { name: 'Реклама', v: g(['Реклама Kaspi', 'Реклама вне Kaspi']) },
      { name: 'Комиссия и доставка Kaspi', v: g(['Комиссия Kaspi', 'Доставка Kaspi']) },
      { name: 'Налог, склад, прочее', v: Object.keys(td).filter(k => !['Выручка', 'Товар: закуп и карго', 'Реклама Kaspi', 'Реклама вне Kaspi', 'Комиссия Kaspi', 'Доставка Kaspi'].includes(k)).reduce((s, k) => s + Math.max(0, -(+td[k] || 0)), 0) },
      { name: 'Прибыль', v: Math.max(0, pnl.net_to_date), color: 'var(--good)' },
    ];
    split = `<div class="card"><b>Куда уходит выручка</b><div class="muted small">из ${compact(rev)} продаж за месяц</div>${segBar(parts, rev)}</div>`;
  }

  const months = [];
  for (let i = 5; i >= 0; i--) {
    const m = shiftMonth(ym(new Date()), -i);
    const v = S.kaspi.filter(k => k.month === m).reduce((s, k) => s + +k.revenue, 0);
    months.push({ v, label: MONTHS[+m.slice(5) - 1].slice(0, 3).toLowerCase(), on: m === S.month, tip: `${monthName(m)} · ${compact(v)}` });
  }
  const next = (c?.upcoming || [])[0];

  return `
    <div class="card hero">
      <div class="muted small">Прибыль бизнеса, ${MONTHS[+S.month.slice(5) - 1].toLowerCase()}</div>
      <div class="hero-v ${pnl && pnl.net_to_date < 0 ? 'neg' : ''}">${pnl ? (pnl.net_to_date >= 0 ? '+' : '') + compact(pnl.net_to_date) : '—'}</div>
      ${pnl ? `<div class="muted small">к концу месяца ожидается ${compact(pnl.net_forecast)}</div>` : '<div class="muted small">Кабинет Kaspi ещё не прислал данные за этот месяц</div>'}
    </div>
    ${c ? `<div class="grid2">
      <div class="card tile"><div class="t-ico">🏦</div><div class="muted small">Деньги компании</div><div class="t-v">${compact(c.cash)}</div></div>
      <div class="card tile"><div class="t-ico">🤝</div><div class="muted small">Компания должна вам</div><div class="t-v">${compact(c.owner_debt)}</div></div>
    </div>` : ''}
    ${split}
    ${products.length ? `<div class="card"><b>Продажи по товарам</b>${rankBars(products)}</div>` : ''}
    <div class="card"><b>Продажи Kaspi по месяцам</b>${columns(months, 'Продажи Kaspi за 6 месяцев')}</div>
    ${next ? `<div class="card row" style="gap:12px"><div class="ico">📅</div><div class="grow"><div class="small muted">Ближайший платёж · ${dayLabel(next.date)}</div><div class="ell">${esc(next.name)}</div></div><b>${compact(next.amount)}</b></div>` : ''}`;
}

function viewHome() {
  const seg = (id, l) => `<button type="button" data-mode="${id}" class="${S.mode === id ? 'on' : ''}">${l}</button>`;
  return `<div class="wrap">
    <div class="row between"><h1>Финансы</h1>${monthNav()}</div>
    ${composer(true)}
    <div class="seg" style="margin-bottom:10px">${seg('personal', '👤 Личное')}${seg('business', '💼 Бизнес')}</div>
    ${S.mode === 'business' ? businessVisual() : personalVisual()}
    <button class="btn ghost" data-act="details">${S.details ? 'Скрыть детали ▲' : 'Подробнее: все цифры ▼'}</button>
    ${S.details ? `<div style="margin-top:12px">${homeDetails()}</div>` : ''}
  </div>`;
}

// tap/hover a mark to see its name and amount
let tipEl = null;
function showTip(el) {
  tipEl?.remove();
  tipEl = document.createElement('div'); tipEl.className = 'tip-pop'; tipEl.textContent = el.dataset.tip;
  document.body.appendChild(tipEl);
  const r = el.getBoundingClientRect(), w = tipEl.offsetWidth;
  tipEl.style.left = Math.max(8, Math.min(innerWidth - w - 8, r.left + r.width / 2 - w / 2)) + 'px';
  tipEl.style.top = (r.top + scrollY - tipEl.offsetHeight - 6) + 'px';
  clearTimeout(showTip.t); showTip.t = setTimeout(() => tipEl?.remove(), 2500);
}

function txRow(t) {
  const c = byId(S.categories, t.category_id), p = byId(S.projects, t.project_id), a = byId(S.accounts, t.account_id);
  const to = byId(S.accounts, t.to_account_id);
  const title = t.type === 'transfer' ? 'Перевод' : (c?.name || (t.type === 'income' ? 'Доход' : 'Расход'));
  const sub = t.type === 'transfer' ? `${esc(a?.name)} → ${esc(to?.name)}` : [p?.name, a?.name].filter(Boolean).map(esc).join(' · ');
  const icon = t.type === 'transfer' ? '🔁' : (c?.icon || '•');
  const cls = t.type === 'income' ? 'pos' : t.type === 'expense' ? '' : 'muted';
  const amt = t.type === 'income' ? money(t.amount, true) : t.type === 'expense' ? money(-t.amount) : money(t.amount);
  return `<div class="item" data-tx="${t.id}"><div class="ico">${icon}</div>
    <div class="grow"><div class="ell">${esc(title)}${t.note ? ` <span class="muted">— ${esc(t.note)}</span>` : ''}</div>
    <div class="muted small ell">${sub}${t.company ? ` · ${t.cabinet_status === 'synced' ? '✓ в кабинете' : '⏳ в кабинет'}` : ''}${t.receipt_path ? ' · 🧾' : ''}</div></div>
    <div class="num ${cls}">${amt}</div></div>`;
}

function viewTxs() {
  let txs = S.txs;
  if (S.filterProject) txs = txs.filter(t => t.project_id === S.filterProject);
  const groups = {};
  for (const t of txs) (groups[t.occurred_on] ||= []).push(t);
  const { inc, exp } = monthTotals(txs);
  return `<div class="wrap">
    <div class="row between"><h1>Операции</h1>${monthNav()}</div>
    <div class="chips"><button class="chip ${!S.filterProject ? 'on' : ''}" data-fp="">Все</button>
      ${S.projects.filter(p => !p.archived).map(p => `<button class="chip ${S.filterProject === p.id ? 'on' : ''}" data-fp="${p.id}">${esc(p.name)}</button>`).join('')}</div>
    <div class="row between small muted" style="margin:10px 4px 0"><span>Доходы <b class="pos num">${money(inc)}</b></span><span>Расходы <b class="neg num">${money(exp)}</b></span></div>
    ${Object.keys(groups).length ? Object.entries(groups).map(([d, list]) => {
      const dayExp = list.filter(t => t.type === 'expense').reduce((s, t) => s + +t.amount, 0);
      return `<div class="daterow"><span>${dayLabel(d)}</span><span class="num">${dayExp ? money(-dayExp) : ''}</span></div>
        <div class="card list" style="padding-top:2px;padding-bottom:2px">${list.map(txRow).join('')}</div>`;
    }).join('') : '<div class="card empty">Операций нет. Нажмите «+», чтобы добавить.</div>'}
  </div>`;
}

function viewAccounts() {
  const active = S.accounts.filter(a => !a.archived), archived = S.accounts.filter(a => a.archived);
  const total = active.reduce((s, a) => s + +a.balance, 0);
  const row = a => {
    const interest = a.kind === 'deposit' && a.interest_rate ? `≈ ${money(a.balance * a.interest_rate / 100 / 12)} в мес. (${a.interest_rate}%)` : '';
    return `<div class="item" data-acc="${a.id}"><div class="ico">${ACC_ICON[a.kind] || '👛'}</div>
      <div class="grow"><div class="ell">${esc(a.name)}${a.last4 ? ` <span class="muted">•${esc(a.last4)}</span>` : ''}</div>
      <div class="muted small ell">${esc(a.bank || '')}${a.balance_source === 'cabinet' ? ' · из кабинета' : ''}${interest ? (a.bank ? ' · ' : '') + interest : ''}</div></div>
      <div class="num ${a.balance < 0 ? 'neg' : ''}">${money(a.balance)}</div></div>`;
  };
  return `<div class="wrap">
    <h1>Счета</h1>
    <div class="card"><div class="muted small">Итого</div><div class="big num">${money(total)}</div></div>
    <div class="card list">${active.map(row).join('')}</div>
    <button class="btn ghost" data-act="new-acc">+ Добавить счёт</button>
    ${archived.length ? `<h2>Архив</h2><div class="card list">${archived.map(row).join('')}</div>` : ''}
    <div class="muted small" style="margin:12px 4px">Чтобы баланс был точным, откройте счёт и укажите текущий остаток на сегодня. Дальше он будет меняться от операций.</div>
  </div>`;
}

function viewProjects() {
  const ps = S.projects.filter(p => !p.archived);
  return `<div class="wrap">
    <div class="row between"><h1>Проекты</h1>${monthNav()}</div>
    ${ps.map(p => {
      const st = projectStats(p);
      return `<div class="card" data-proj="${p.id}" style="cursor:pointer">
        <div class="row between"><div class="row"><span class="dot" style="background:${esc(p.color)}"></span><b>${esc(p.name)}</b></div>
        ${p.kind === 'business' ? `<b class="num ${st.profit >= 0 ? 'pos' : 'neg'}">${money(st.profit, true)}</b>` : `<b class="num">${money(-st.exp)}</b>`}</div>
        <div class="muted small" style="margin-top:4px">
          ${st.k.revenue ? `Kaspi ${money(st.k.revenue)} (${st.k.units} шт) · ` : ''}${st.inc ? `доходы ${money(st.inc)} · ` : ''}расходы ${money(st.exp)}
        </div></div>`;
    }).join('')}
    <button class="btn ghost" data-act="new-proj">+ Новый проект</button>

    <h2>Бюджеты на месяц</h2>
    <div class="card list">${S.budgets.length ? S.budgets.map(b => {
      const u = budgetUsage(b);
      const col = u.pct >= 1 ? '--neg' : u.pct >= 0.8 ? '--warn' : '--pos';
      return `<div class="item" data-bud="${b.id}"><div class="grow"><div class="row between"><span class="ell">${esc(budgetName(b))}</span>
        <span class="num small">${money(u.spent)} / ${money(b.monthly_limit)}</span></div>
        <div class="bar"><i style="width:${Math.min(100, u.pct * 100)}%;background:var(${col})"></i></div></div></div>`;
    }).join('') : '<div class="muted">Бюджетов нет. Задайте лимит, и я предупрежу, когда он будет близко.</div>'}</div>
    <button class="btn ghost" data-act="new-bud">+ Бюджет</button>
  </div>`;
}

function render() {
  if (!S.session) return renderAuth();
  if (!S.owner) {
    $('#app').innerHTML = `<div class="auth"><img class="logo" src="icon.svg" alt=""><h1 style="text-align:center">Нет доступа</h1>
      <p class="muted" style="text-align:center">Этот аккаунт не является владельцем данных.</p>
      <button class="btn ghost" data-act="logout">Выйти</button></div>`;
    return;
  }
  const v = { home: viewHome, txs: viewTxs, accounts: viewAccounts, projects: viewProjects }[S.tab]();
  const tab = (id, label, icon) => `<button class="${S.tab === id ? 'on' : ''}" data-tab="${id}">${icon}<span>${label}</span></button>`;
  $('#app').innerHTML = v + (S.tab === 'home' ? '' : composer()) + `<nav class="tabs">${tab('home', 'Обзор', I.home)}${tab('txs', 'Операции', I.list)}
    <button class="add" data-act="new-tx" aria-label="Добавить операцию">${I.plus}</button>
    ${tab('accounts', 'Счета', I.card)}${tab('projects', 'Проекты', I.folder)}</nav>`;
}

/* ---------- smart input ---------- */
function composer(inline) {
  const d = S.draft;
  return `<div class="composer${inline ? ' inline card' : ''}">
    ${inline ? '<div class="row between" style="margin-bottom:8px"><b>Записать или спросить</b><span class="muted small">текст, голос или чек</span></div>' : ''}
    ${d.files.length ? `<div class="chips" style="margin-bottom:6px">${d.files.map((f, i) => `<span class="chip">${f.type === 'application/pdf' ? '📄' : '🖼'} ${esc(f.name.slice(0, 18))} <button class="link" data-rmfile="${i}" aria-label="Убрать">✕</button></span>`).join('')}</div>` : ''}
    <div class="row" style="gap:8px;align-items:flex-end">
      <label class="cbtn" aria-label="Прикрепить чек">📎<input type="file" id="cfile" accept="image/*,application/pdf" multiple hidden></label>
      <textarea id="ctext" rows="1" placeholder="${inline ? 'Например: такси 3500 налом' : 'Трата, чек или вопрос…'}" ${S.sending ? 'disabled' : ''}>${esc(d.text)}</textarea>
      <button class="cbtn send" data-act="send" ${S.sending ? 'disabled' : ''} aria-label="Отправить">${S.sending ? '<span class="spin"></span>' : '↑'}</button>
    </div>
  </div>`;
}
function autosize(t) { t.style.height = 'auto'; t.style.height = Math.min(t.scrollHeight, 140) + 'px'; }

// iPhone photos (HEIC, 12 MP) -> JPEG up to 2000 px, so uploads stay small and the AI can read them
async function prepareFile(file) {
  if (file.type === 'application/pdf') return { blob: file, ext: 'pdf', type: 'application/pdf' };
  const url = URL.createObjectURL(file);
  try {
    const img = await new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = url; });
    const k = Math.min(1, 2000 / Math.max(img.naturalWidth, img.naturalHeight));
    const c = document.createElement('canvas');
    c.width = Math.round(img.naturalWidth * k); c.height = Math.round(img.naturalHeight * k);
    c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
    const blob = await new Promise(res => c.toBlob(res, 'image/jpeg', 0.85));
    return { blob, ext: 'jpg', type: 'image/jpeg' };
  } finally { URL.revokeObjectURL(url); }
}

async function sendDraft() {
  const text = S.draft.text.trim(), files = S.draft.files;
  if (!text && !files.length) return toast('Напишите сообщение или прикрепите чек');
  S.sending = true; render();
  try {
    const paths = [];
    for (const f of files) {
      const { blob, ext, type } = await prepareFile(f);
      const path = `${today().slice(0, 7)}/${crypto.randomUUID()}.${ext}`;
      const { error } = await sb.storage.from('fin-receipts').upload(path, blob, { contentType: type });
      if (error) throw new Error('Не удалось загрузить файл: ' + error.message);
      paths.push(path);
    }
    const { data, error } = await sb.functions.invoke('fin-assistant', { body: { text, files: paths, today: today() } });
    if (error) {
      let msg = error.message;
      try { msg = (await error.context.json()).error || msg; } catch (_) {}
      throw new Error(msg);
    }
    S.draft = { text: '', files: [] };
    S.sending = false;
    await reloadAll();
    resultSheet(data);
  } catch (e) {
    S.sending = false; render();
    toast(e.message || 'Ошибка');
  }
}

function resultSheet(r) {
  const txs = r.transactions || [];
  openSheet(`<div class="row" style="gap:10px;align-items:flex-start"><div class="ico">🤖</div><div class="grow" style="padding-top:6px">${esc(r.reply)}</div></div>
    ${txs.length ? `<h2>Записано</h2><div class="card list">${txs.map(txRow).join('')}</div>` : ''}
    ${(r.balances || []).map(b => `<div class="card small">Остаток «${esc(b.account)}»: <b class="num">${money(b.balance)}</b></div>`).join('')}
    <button class="btn" type="button" data-ok>Готово</button>
    ${txs.length ? `<button class="btn danger" type="button" data-undo>Отменить запись</button>` : ''}`, (el, close) => {
    el.querySelector('[data-ok]').onclick = close;
    el.querySelectorAll('[data-tx]').forEach(n => n.onclick = () => { close(); txSheet(txs.find(t => t.id === n.dataset.tx)); });
    const undo = el.querySelector('[data-undo]');
    if (undo) undo.onclick = async () => {
      const ids = txs.map(t => t.id);
      const d = await sb.from('fin_transactions').delete().in('id', ids);
      if (d.error) return toast('Ошибка: ' + d.error.message);
      await sb.from('fin_inbox').update({ status: 'undone' }).eq('id', r.inbox_id);
      close(); toast('Отменено'); reloadAll();
    };
  });
}

/* ---------- auth ---------- */
function renderAuth(mode = 'in', msg = '') {
  $('#app').innerHTML = `<div class="auth">
    <img class="logo" src="icon.svg" alt=""><h1 style="text-align:center">Финансы</h1>
    <form id="authf">
      <label class="field"><span>Email</span><input name="email" type="email" autocomplete="username" required></label>
      <label class="field"><span>Пароль</span><input name="password" type="password" autocomplete="${mode === 'in' ? 'current-password' : 'new-password'}" minlength="8" required></label>
      <button class="btn" type="submit">${mode === 'in' ? 'Войти' : 'Создать аккаунт'}</button>
    </form>
    ${msg ? `<p class="small" style="text-align:center">${esc(msg)}</p>` : ''}
    <p style="text-align:center"><button class="link" data-auth="${mode === 'in' ? 'up' : 'in'}">${mode === 'in' ? 'Первый вход? Создать аккаунт' : 'Уже есть аккаунт? Войти'}</button></p>
  </div>`;
  $('#authf').onsubmit = async e => {
    e.preventDefault();
    const f = new FormData(e.target), email = f.get('email').trim(), password = f.get('password');
    const btn = e.target.querySelector('button'); btn.disabled = true;
    const r = mode === 'in' ? await sb.auth.signInWithPassword({ email, password }) : await sb.auth.signUp({ email, password });
    btn.disabled = false;
    if (r.error) return renderAuth(mode, r.error.message);
    if (mode === 'up' && !r.data.session) return renderAuth('in', 'Мы отправили письмо: подтвердите email и войдите.');
  };
}
async function onSession(session) {
  S.session = session;
  if (!session) { S.owner = false; return render(); }
  const { data } = await sb.rpc('fin_claim_owner');
  S.owner = !!data;
  if (S.owner) await reloadAll(); else render();
}

/* ---------- sheets ---------- */
function openSheet(html, bind) {
  const bg = document.createElement('div'); bg.className = 'sheet-bg';
  bg.innerHTML = `<div class="sheet"><div class="grab"></div>${html}</div>`;
  bg.addEventListener('click', e => { if (e.target === bg) bg.remove(); });
  document.body.appendChild(bg);
  bind(bg.querySelector('.sheet'), () => bg.remove());
}
const opts = (arr, sel, empty) => (empty ? `<option value="">${empty}</option>` : '') +
  arr.map(x => `<option value="${x.id}" ${x.id === sel ? 'selected' : ''}>${esc(x.icon ? x.icon + ' ' + x.name : x.name)}</option>`).join('');

function txSheet(tx) {
  const t = tx || { type: 'expense', occurred_on: today(), account_id: S.accounts.find(a => !a.archived)?.id, project_id: S.filterProject || S.projects[0]?.id };
  let type = t.type;
  const accs = S.accounts.filter(a => !a.archived || a.id === t.account_id || a.id === t.to_account_id);
  openSheet(`
    <div class="seg">${[['expense', 'Расход'], ['income', 'Доход'], ['transfer', 'Перевод']].map(([k, l]) => `<button type="button" data-type="${k}" class="${type === k ? 'on' : ''}">${l}</button>`).join('')}</div>
    <form id="txf">
      <input class="amount num" name="amount" inputmode="decimal" placeholder="0 ₸" value="${tx ? Math.round(t.amount * 100) / 100 : ''}" autocomplete="off" required>
      <label class="field"><span id="acc-l">Счёт</span><select name="account_id">${opts(accs, t.account_id)}</select></label>
      <label class="field" id="to-f"><span>На счёт</span><select name="to_account_id">${opts(accs.filter(a => a.id !== t.account_id), t.to_account_id)}</select></label>
      <label class="field" id="proj-f"><span>Проект</span><select name="project_id">${opts(S.projects.filter(p => !p.archived || p.id === t.project_id), t.project_id, '—')}</select></label>
      <label class="field" id="cat-f"><span>Категория</span><select name="category_id"></select></label>
      <label class="field"><span>Дата</span><input type="date" name="occurred_on" value="${t.occurred_on}" required></label>
      <label class="field"><span>Комментарий</span><input name="note" value="${esc(t.note || '')}" placeholder="необязательно"></label>
      <label class="field row" id="co-f" style="gap:10px"><input type="checkbox" name="company" ${t.company ? 'checked' : ''} style="width:auto"><span style="font-size:15px;color:var(--text)">Расход компании (передать в кабинет Kaspi)</span></label>
      ${tx?.receipt_path ? `<button class="btn ghost" type="button" data-receipt>🧾 Показать чек</button>` : ''}
      <button class="btn" type="submit">${tx ? 'Сохранить' : 'Добавить'}</button>
      ${tx ? `<button class="btn danger" type="button" data-del>Удалить</button>` : ''}
    </form>`, (el, close) => {
    const f = el.querySelector('#txf');
    const sync = () => {
      el.querySelectorAll('[data-type]').forEach(b => b.classList.toggle('on', b.dataset.type === type));
      el.querySelector('#to-f').style.display = type === 'transfer' ? '' : 'none';
      el.querySelector('#proj-f').style.display = type === 'transfer' ? 'none' : '';
      el.querySelector('#cat-f').style.display = type === 'transfer' ? 'none' : '';
      el.querySelector('#acc-l').textContent = type === 'transfer' ? 'Со счёта' : 'Счёт';
      el.querySelector('#co-f').style.display = type === 'transfer' ? 'none' : '';
      const cur = f.category_id.value || t.category_id;
      f.category_id.innerHTML = opts(S.categories.filter(c => c.type === (type === 'income' ? 'income' : 'expense')), cur, '—');
    };
    el.querySelectorAll('[data-type]').forEach(b => b.onclick = () => { type = b.dataset.type; sync(); });
    f.account_id.onchange = () => {
      const keep = f.to_account_id.value;
      f.to_account_id.innerHTML = opts(accs.filter(a => a.id !== f.account_id.value), keep);
    };
    sync();
    if (!tx) setTimeout(() => f.amount.focus(), 250);
    f.onsubmit = async e => {
      e.preventDefault();
      const amount = parseAmount(f.amount.value);
      if (!(amount > 0)) return toast('Введите сумму');
      const row = {
        type, amount, occurred_on: f.occurred_on.value, account_id: f.account_id.value,
        to_account_id: type === 'transfer' ? f.to_account_id.value || null : null,
        project_id: type === 'transfer' ? null : f.project_id.value || null,
        category_id: type === 'transfer' ? null : f.category_id.value || null,
        note: f.note.value.trim() || null,
        company: type !== 'transfer' && f.company.checked,
      };
      // company rows go to the cabinet; an edit of one already there is sent again so the cabinet updates it
      const changed = !tx || ['type', 'amount', 'occurred_on', 'account_id', 'note', 'company'].some(k => String(tx[k] ?? '') !== String(row[k] ?? ''));
      if (row.company && changed) row.cabinet_status = 'pending';
      if (!row.company && tx?.company && tx.cabinet_status === 'synced') row.cabinet_status = 'pending';
      if (!row.company && !(tx?.company && tx.cabinet_status === 'synced')) row.cabinet_status = null;
      if (type === 'transfer' && !row.to_account_id) return toast('Выберите счёт получателя');
      const r = tx ? await sb.from('fin_transactions').update(row).eq('id', tx.id) : await sb.from('fin_transactions').insert({ ...row, source: 'app' });
      if (r.error) return toast('Ошибка: ' + r.error.message);
      close(); toast(tx ? 'Сохранено' : 'Добавлено');
      if (row.occurred_on.slice(0, 7) !== S.month) S.month = row.occurred_on.slice(0, 7);
      reloadAll();
    };
    const rc = el.querySelector('[data-receipt]');
    if (rc) rc.onclick = async () => {
      const { data, error } = await sb.storage.from('fin-receipts').createSignedUrl(tx.receipt_path, 300);
      if (error) return toast('Не удалось открыть чек');
      window.open(data.signedUrl, '_blank');
    };
    const del = el.querySelector('[data-del]');
    if (del) del.onclick = async () => {
      if (!confirm(tx.cabinet_status === 'synced' ? 'Операция уже передана в кабинет Kaspi. Удалить здесь? В кабинете её нужно будет убрать отдельно (скажите об этом чату Kaspi).' : 'Удалить операцию?')) return;
      const r = await sb.from('fin_transactions').delete().eq('id', tx.id);
      if (r.error) return toast('Ошибка: ' + r.error.message);
      close(); toast('Удалено'); reloadAll();
    };
  });
}

function accSheet(a) {
  const x = a ? { ...a, ...S.accounts.find(z => z.id === a.id) } : { kind: 'card', opening_balance: 0, opening_date: today() };
  const loadFull = a ? sb.from('fin_accounts').select('*').eq('id', a.id).single() : Promise.resolve({ data: x });
  loadFull.then(({ data }) => {
    const acc = data || x;
    openSheet(`<h1 style="font-size:22px">${a ? 'Счёт' : 'Новый счёт'}</h1>
      ${a ? `<div class="card"><div class="muted small">Текущий баланс</div><div class="big num">${money(a.balance)}</div></div>` : ''}
      <form id="accf">
        <label class="field"><span>Название</span><input name="name" value="${esc(acc.name || '')}" required></label>
        <label class="field"><span>Тип</span><select name="kind">${[['card', 'Карта'], ['business', 'Бизнес-счёт'], ['deposit', 'Депозит'], ['cash', 'Наличные'], ['other', 'Другое']].map(([k, l]) => `<option value="${k}" ${acc.kind === k ? 'selected' : ''}>${l}</option>`).join('')}</select></label>
        <label class="field"><span>Банк</span><input name="bank" value="${esc(acc.bank || '')}"></label>
        <label class="field"><span>Последние 4 цифры (необязательно)</span><input name="last4" inputmode="numeric" maxlength="4" pattern="[0-9]{4}" value="${esc(acc.last4 || '')}"></label>
        ${a?.balance_source === 'cabinet' ? `<div class="card small muted">Остаток этого счёта берётся из кабинета Kaspi. Меняйте его там.</div>`
          : a ? `<label class="field"><span>Установить текущий остаток, ₸</span><input name="set_balance" inputmode="decimal" placeholder="${Math.round(a.balance)}"></label>`
            : `<label class="field"><span>Остаток сейчас, ₸</span><input name="opening_balance" inputmode="decimal" value="0"></label>`}
        <label class="field"><span>Ставка депозита, % годовых</span><input name="interest_rate" inputmode="decimal" value="${acc.interest_rate ?? ''}"></label>
        <label class="field"><span>Заметка</span><input name="note" value="${esc(acc.note || '')}"></label>
        <button class="btn" type="submit">Сохранить</button>
        ${a ? `<button class="btn ghost" type="button" data-arch>${acc.archived ? 'Вернуть из архива' : 'В архив'}</button>` : ''}
      </form>`, (el, close) => {
      const f = el.querySelector('#accf');
      f.onsubmit = async e => {
        e.preventDefault();
        const row = { name: f.name.value.trim(), kind: f.kind.value, bank: f.bank.value.trim() || null, last4: f.last4.value.trim() || null,
          interest_rate: f.interest_rate.value ? parseAmount(f.interest_rate.value) : null, note: f.note.value.trim() || null };
        let r;
        if (a) {
          if (f.set_balance && f.set_balance.value.trim() !== '') {
            // Новый остаток на сегодня: стартовая точка переносится на сегодня, старые операции остаются в истории.
            const target = parseAmount(f.set_balance.value);
            const { data: todays } = await sb.from('fin_transactions').select('type,amount,account_id,to_account_id').eq('occurred_on', today()).or(`account_id.eq.${a.id},to_account_id.eq.${a.id}`);
            let delta = 0;
            for (const t of todays || []) {
              if (t.account_id === a.id) delta += t.type === 'income' ? +t.amount : -t.amount;
              if (t.to_account_id === a.id && t.type === 'transfer') delta += +t.amount;
            }
            row.opening_balance = target - delta; row.opening_date = today();
          }
          r = await sb.from('fin_accounts').update(row).eq('id', a.id);
        } else {
          row.slug = 'acc-' + Date.now().toString(36);
          row.opening_balance = parseAmount(f.opening_balance.value) || 0; row.opening_date = today(); row.sort = 100;
          r = await sb.from('fin_accounts').insert(row);
        }
        if (r.error) return toast('Ошибка: ' + r.error.message);
        close(); toast('Сохранено'); reloadAll();
      };
      const arch = el.querySelector('[data-arch]');
      if (arch) arch.onclick = async () => {
        const r = await sb.from('fin_accounts').update({ archived: !acc.archived }).eq('id', a.id);
        if (r.error) return toast('Ошибка: ' + r.error.message);
        close(); reloadAll();
      };
    });
  });
}

function projSheet(p) {
  const x = p || { kind: 'business', color: '#64748b' };
  openSheet(`<h1 style="font-size:22px">${p ? esc(p.name) : 'Новый проект'}</h1>
    <form id="pf">
      <label class="field"><span>Название</span><input name="name" value="${esc(x.name || '')}" required></label>
      <label class="field"><span>Тип</span><select name="kind"><option value="business" ${x.kind === 'business' ? 'selected' : ''}>Бизнес</option><option value="personal" ${x.kind === 'personal' ? 'selected' : ''}>Личное</option></select></label>
      <label class="field"><span>Цвет</span><input type="color" name="color" value="${esc(x.color)}" style="height:34px"></label>
      <button class="btn" type="submit">Сохранить</button>
      ${p ? `<button class="btn ghost" type="button" data-show>Показать операции</button><button class="btn danger" type="button" data-arch>В архив</button>` : ''}
    </form>`, (el, close) => {
    const f = el.querySelector('#pf');
    f.onsubmit = async e => {
      e.preventDefault();
      const row = { name: f.name.value.trim(), kind: f.kind.value, color: f.color.value };
      const r = p ? await sb.from('fin_projects').update(row).eq('id', p.id)
        : await sb.from('fin_projects').insert({ ...row, slug: 'p-' + Date.now().toString(36), sort: 100 });
      if (r.error) return toast('Ошибка: ' + r.error.message);
      close(); reloadAll();
    };
    const show = el.querySelector('[data-show]');
    if (show) show.onclick = () => { close(); S.filterProject = p.id; S.tab = 'txs'; render(); };
    const arch = el.querySelector('[data-arch]');
    if (arch) arch.onclick = async () => {
      if (!confirm('Убрать проект в архив? Операции останутся.')) return;
      const r = await sb.from('fin_projects').update({ archived: true }).eq('id', p.id);
      if (r.error) return toast('Ошибка: ' + r.error.message);
      close(); reloadAll();
    };
  });
}

function budSheet(b) {
  const x = b || {};
  openSheet(`<h1 style="font-size:22px">${b ? 'Бюджет' : 'Новый бюджет'}</h1>
    <form id="bf">
      <label class="field"><span>Проект</span><select name="project_id">${opts(S.projects.filter(p => !p.archived), x.project_id, 'Все проекты')}</select></label>
      <label class="field"><span>Категория</span><select name="category_id">${opts(S.categories.filter(c => c.type === 'expense'), x.category_id, 'Все категории')}</select></label>
      <label class="field"><span>Лимит в месяц, ₸</span><input name="limit" inputmode="decimal" value="${x.monthly_limit ? Math.round(x.monthly_limit) : ''}" required></label>
      <button class="btn" type="submit">Сохранить</button>
      ${b ? `<button class="btn danger" type="button" data-del>Удалить</button>` : ''}
    </form>`, (el, close) => {
    const f = el.querySelector('#bf');
    f.onsubmit = async e => {
      e.preventDefault();
      const row = { project_id: f.project_id.value || null, category_id: f.category_id.value || null, monthly_limit: parseAmount(f.limit.value) };
      if (!(row.monthly_limit > 0)) return toast('Введите лимит');
      const r = b ? await sb.from('fin_budgets').update(row).eq('id', b.id) : await sb.from('fin_budgets').insert(row);
      if (r.error) return toast(r.error.code === '23505' ? 'Такой бюджет уже есть' : 'Ошибка: ' + r.error.message);
      close(); reloadAll();
    };
    const del = el.querySelector('[data-del]');
    if (del) del.onclick = async () => {
      const r = await sb.from('fin_budgets').delete().eq('id', b.id);
      if (r.error) return toast('Ошибка: ' + r.error.message);
      close(); reloadAll();
    };
  });
}

/* ---------- events ---------- */
document.addEventListener('click', async e => {
  const tipT = e.target.closest('[data-tip]');
  if (tipT) showTip(tipT);
  const md = e.target.closest('[data-mode]');
  if (md) { S.mode = md.dataset.mode; try { localStorage.setItem('fin-mode', S.mode); } catch (_) {} render(); return; }
  const rm = e.target.closest('[data-rmfile]');
  if (rm) { S.draft.files.splice(+rm.dataset.rmfile, 1); render(); return; }
  const el = e.target.closest('[data-tab],[data-act],[data-tx],[data-acc],[data-proj],[data-bud],[data-fp],[data-go],[data-auth]');
  if (!el || el.closest('.sheet')) return;
  const d = el.dataset;
  if (d.auth) return renderAuth(d.auth);
  if (d.tab) { S.tab = d.tab; render(); window.scrollTo(0, 0); return; }
  if (d.go) { S.tab = d.go; render(); return; }
  if (d.fp !== undefined) { S.filterProject = d.fp || null; render(); return; }
  if (d.tx) return txSheet(byId(S.txs, d.tx));
  if (d.acc) return accSheet(byId(S.accounts, d.acc));
  if (d.proj) return projSheet(byId(S.projects, d.proj));
  if (d.bud) return budSheet(byId(S.budgets, d.bud));
  switch (d.act) {
    case 'prev': S.month = shiftMonth(S.month, -1); await loadMonth().catch(() => {}); return render();
    case 'next': S.month = shiftMonth(S.month, 1); await loadMonth().catch(() => {}); return render();
    case 'new-tx': return txSheet(null);
    case 'send': return sendDraft();
    case 'details': S.details = !S.details; return render();
    case 'new-acc': return accSheet(null);
    case 'new-proj': return projSheet(null);
    case 'new-bud': return budSheet(null);
    case 'logout': await sb.auth.signOut(); return;
  }
});
document.addEventListener('input', e => {
  if (e.target.id === 'ctext') { S.draft.text = e.target.value; autosize(e.target); }
});
document.addEventListener('change', e => {
  if (e.target.id === 'cfile') { S.draft.files.push(...e.target.files); render(); }
});
document.addEventListener('keydown', e => {
  // Enter sends on a computer; on iPhone Enter is a new line
  if (e.target.id === 'ctext' && e.key === 'Enter' && !e.shiftKey && !('ontouchstart' in window)) { e.preventDefault(); sendDraft(); }
});
document.addEventListener('visibilitychange', () => { if (!document.hidden && S.owner && !S.sending) reloadAll(); });

sb.auth.onAuthStateChange((event, session) => {
  if (event === 'INITIAL_SESSION' || event === 'SIGNED_IN' || event === 'SIGNED_OUT') {
    if ((session?.user?.id || null) !== (S.session?.user?.id || null) || event === 'INITIAL_SESSION') setTimeout(() => onSession(session), 0);
  } else if (session) S.session = session;
});
// Auto-update: the home-screen app checks for a new release on start, every minute and on return,
// and reloads itself, so the user never has to reinstall it.
async function checkUpdate() {
  if (S.sending || document.querySelector('.sheet-bg')) return; // never interrupt typing or an open form
  try {
    const r = await fetch('version.json?t=' + Date.now(), { cache: 'no-store' });
    const { v } = await r.json();
    if (v && v !== APP_VERSION) {
      // one reload per release: if a cache still serves the old file, don't loop
      let tried = null; try { tried = sessionStorage.getItem('fin-reload'); } catch (_) {}
      if (tried === v) return;
      try { sessionStorage.setItem('fin-reload', v); } catch (_) {}
      const reg = await navigator.serviceWorker?.getRegistration();
      await reg?.update().catch(() => {});
      location.reload();
    }
  } catch (_) {}
}
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js', { updateViaCache: 'none' }).catch(() => {});
}
checkUpdate();
setInterval(checkUpdate, 60000);
document.addEventListener('visibilitychange', () => { if (!document.hidden) checkUpdate(); });
