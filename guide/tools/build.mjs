// Static site generator: content.json (+ content.kk.json overlay) -> real HTML pages in Russian and Kazakh.
// Run from the guide/ folder: node tools/build.mjs
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(import.meta.dirname, "..");
const BASE = JSON.parse(fs.readFileSync(path.join(ROOT, "content.json"), "utf8"));
const KK = JSON.parse(fs.readFileSync(path.join(ROOT, "content.kk.json"), "utf8"));
const API = "https://jarvis-backend-alisher25.vercel.app";
const SITE = "https://ataria-guide.vercel.app";

// Overlay merge: objects by key, arrays of objects by index, arrays of strings replaced.
function merge(base, over) {
  if (over === undefined) return base;
  if (Array.isArray(base)) {
    if (base.length && typeof base[0] === "object") return base.map((b, i) => merge(b, over[i]));
    return over;
  }
  if (base && typeof base === "object") {
    const out = { ...base };
    for (const k of Object.keys(over)) out[k] = merge(base[k], over[k]);
    return out;
  }
  return over;
}

const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const splitIng = (s) => { const [n, ...rest] = s.split(" — "); return rest.length ? [n, rest.join(" — ")] : [s, ""]; };

const ICONS = {
  hook: '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"><rect x="24" y="6" width="16" height="7" rx="3"/><path d="M32 13v16c0 9 11 9 11 18 0 7-7 11-14 8"/><path d="M32 13v8"/></svg>',
  beater: '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"><rect x="25" y="5" width="14" height="7" rx="3"/><path d="M32 12v8"/><path d="M32 20c-13 4-17 15-13 27 2 6 8 10 13 10s11-4 13-10c4-12 0-23-13-27z"/><path d="M32 30v26M32 38l-8 9M32 38l8 9"/></svg>',
  whisk: '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"><rect x="26" y="4" width="12" height="9" rx="3"/><path d="M32 13v7"/><path d="M32 20c-15 5-17 28 0 38 17-10 15-33 0-38z"/><path d="M32 20c-7 9-7 29 0 38M32 20c7 9 7 29 0 38M19 33h26M18 45h28"/></svg>',
  slicer: '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.3"><rect x="10" y="20" width="44" height="26" rx="13"/><circle cx="22" cy="33" r="1.4"/><circle cx="30" cy="29" r="1.4"/><circle cx="38" cy="33" r="1.4"/><circle cx="46" cy="29" r="1.4"/><circle cx="26" cy="38" r="1.4"/><circle cx="34" cy="38" r="1.4"/><circle cx="42" cy="38" r="1.4"/><path d="M6 33h4M54 33h4"/></svg>',
  roller: '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.3"><rect x="12" y="16" width="40" height="12" rx="6"/><rect x="12" y="30" width="40" height="12" rx="6"/><path d="M18 50c6-3 22-3 28 0M6 22h6M52 36h6"/></svg>',
  noodle: '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.3"><rect x="10" y="12" width="44" height="14" rx="7"/><path d="M18 30c0 10 2 18 0 24M26 30c0 10-2 18 0 24M34 30c0 10 2 18 0 24M42 30c0 10-2 18 0 24"/></svg>',
  airfryer: '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.2"><rect x="14" y="8" width="36" height="48" rx="14"/><rect x="20" y="30" width="24" height="18" rx="5"/><circle cx="32" cy="19" r="4"/><path d="M28 56v2M36 56v2"/></svg>',
  clock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  people: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.5 2.7-6 6-6s6 2.5 6 6"/><circle cx="17" cy="9" r="2.4"/><path d="M16 14.2c3 0 5 2 5 5"/></svg>',
  search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/></svg>',
  menu: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M4 8h16M4 16h16"/></svg>',
  speed: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M4 17a8 8 0 1 1 16 0"/><path d="m12 17 4-6"/></svg>',
  parts: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><rect x="4" y="4" width="7" height="7" rx="2"/><rect x="13" y="4" width="7" height="7" rx="2"/><rect x="4" y="13" width="7" height="7" rx="2"/><rect x="13" y="13" width="7" height="7" rx="2"/></svg>',
  book: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M5 5.5C7.5 4.5 10 4.5 12 6c2-1.5 4.5-1.5 7-.5V19c-2.5-1-5-1-7 .5-2-1.5-4.5-1.5-7-.5z"/><path d="M12 6v13.5"/></svg>',
  care: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M12 3c3 4 6 6.5 6 10a6 6 0 0 1-12 0c0-3.5 3-6 6-10z"/></svg>',
  help: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.4-1 .9-1 1.7M12 17v.2"/></svg>',
};

const files = new Map();
const pageUrls = [];

function buildSite(lang) {
  const kk = lang === "kk";
  const T = (ru, k) => (kk ? k : ru);
  const P = kk ? "/kk" : "";
  const DATA = kk ? merge(BASE, KK) : BASE;
  const WA = API + DATA.support.whatsapp;
  const KASPI_REVIEW = DATA.support.kaspi_review;
  const KASPI_CARD = DATA.support.kaspi_card;
  const sm = DATA.products.find((p) => p.id === "sm23");
  const af = DATA.products.find((p) => p.id === "airfryer");
  const att = (p, id) => p.attachments.find((a) => a.id === id);
  const minutesLabel = (m) => (m >= 60 ? `${Math.floor(m / 60)} ${T("ч", "сағ")}${m % 60 ? " " + (m % 60) + " " + T("мин", "мин") : ""}` : `${m} ${T("мин", "мин")}`);
  const media = (item) => (item.image ? `<img src="/${esc(item.image)}" alt="${esc(item.name || item.title)}" loading="lazy">` : ICONS[item.id] || "");
  const emit = (url, html) => { files.set(path.join(`${P}${url}`.slice(1) || ".", "index.html"), html); pageUrls.push(`${P}${url}`); };

  const productNav = (p, active) => [
    ["", T("Главная", "Басты бет")], ["about", T("О машине", "Машина туралы")], ["start", T("С чего начать", "Қалай бастау керек")], ["speeds", T("Скорости", "Жылдамдықтар")],
    ["attachments", T("Насадки", "Қондырмалар")], ["recipes", T("Рецепты", "Рецепттер")], ["care", T("Уход", "Күтім")], ["help", T("Помощь", "Көмек")],
  ].map(([k, l]) => ({ k, l, href: `${P}/${p.id}/${k ? k + "/" : ""}`, on: active === k }));

  function header(active, url) {
    const switchHtml = `<div class="lang" role="group" aria-label="Тіл / Язык"><a href="${url}" class="${kk ? "" : "on"}" hreflang="ru" data-lang="ru">RU</a><a href="/kk${url}" class="${kk ? "on" : ""}" hreflang="kk" data-lang="kk">ҚАЗ</a></div>`;
    return `<header class="top">
  <div class="top-in">
    <a href="${P}/" class="logo" aria-label="ATARIA"><img src="/img/logo.png" alt="ATARIA" width="64" height="44"></a>
    <nav class="topnav" aria-label="${T("Разделы", "Бөлімдер")}">
      <div class="dd">
        <a href="${P}/sm23/" class="${active !== null && active !== "recipes" && active !== "attachments" ? "on" : ""}">${T("Кухонная машина", "Асүй комбайны")}</a>
        <div class="dd-menu">${productNav(sm, "").map((x) => `<a href="${x.href}">${x.l}</a>`).join("")}</div>
      </div>
      <a href="${P}/sm23/recipes/" class="${active === "recipes" ? "on" : ""}">${T("Рецепты", "Рецепттер")}</a>
      <a href="${P}/sm23/attachments/" class="${active === "attachments" ? "on" : ""}">${T("Насадки", "Қондырмалар")}</a>
      <a href="${P}/airfryer/" class="soon-link">Аэрогриль <i>${T("скоро", "жақында")}</i></a>
    </nav>
    <div class="top-act">
      ${switchHtml}
      <button class="icon-btn" id="open-search" aria-label="${T("Поиск", "Іздеу")}">${ICONS.search}</button>
      <a class="btn sm" href="${esc(WA)}" target="_blank" rel="noopener">WhatsApp</a>
      <button class="icon-btn menu-btn" id="open-menu" aria-label="${T("Меню", "Мәзір")}">${ICONS.menu}</button>
    </div>
  </div>
</header>
<div class="drawer" id="drawer" hidden>
  <div class="drawer-in">
    <button class="x" id="close-menu">${T("Закрыть", "Жабу")}</button>
    <p class="eyebrow">${T("Кухонная машина AT-SM23", "Асүй комбайны AT-SM23")}</p>
    ${productNav(sm, "").map((x) => `<a href="${x.href}">${x.l}</a>`).join("")}
    <p class="eyebrow" style="margin-top:22px">${T("Скоро", "Жақында")}</p>
    <a href="${P}/airfryer/">${esc(af.name)}</a>
    <a class="btn" style="margin-top:22px" href="${esc(WA)}" target="_blank" rel="noopener">${T("Написать в WhatsApp", "WhatsApp-қа жазу")}</a>
  </div>
</div>
<div class="search" id="search" hidden data-empty="${T("Ничего не нашли. Напишите нам в WhatsApp, подскажем.", "Ештеңе табылмады. WhatsApp-қа жазыңыз, көмектесеміз.")}">
  <div class="search-in">
    <div class="search-bar">${ICONS.search}<input id="q" type="search" placeholder="${T("Например: тесто, мясорубка, скорость", "Мысалы: қамыр, ет тартқыш, жылдамдық")}" autocomplete="off"><button class="x" id="close-search">${T("Закрыть", "Жабу")}</button></div>
    <div id="results" class="results"></div>
  </div>
</div>`;
  }

  function footer() {
    return `<footer class="foot">
  <div class="foot-in">
    <div class="foot-brand"><a href="${P}/" class="logo-full" aria-label="ATARIA"><img src="/img/logo.png" alt="ATARIA" width="120" height="83"></a><p>${T("Рецепты, насадки и простые советы для вашей техники. Казахстан.", "Техникаңызға арналған рецепттер, қондырмалар және қарапайым кеңестер. Қазақстан.")}</p></div>
    <div><p class="eyebrow">${T("Кухонная машина", "Асүй комбайны")}</p>${productNav(sm, "").map((x) => `<a href="${x.href}">${x.l}</a>`).join("")}</div>
    <div><p class="eyebrow">${T("Рецепты", "Рецепттер")}</p>${sm.recipes.slice(0, 5).map((r) => `<a href="${P}/sm23/recipes/${r.id}/">${esc(r.title)}</a>`).join("")}<a href="${P}/sm23/recipes/">${T("Все рецепты", "Барлық рецепттер")}</a></div>
    <div><p class="eyebrow">${T("Связь", "Байланыс")}</p><a href="${esc(WA)}" target="_blank" rel="noopener">${T("Поддержка в WhatsApp", "WhatsApp қолдауы")}</a>${KASPI_CARD ? `<a href="${esc(KASPI_CARD)}" target="_blank" rel="noopener">${T("Карточка на Kaspi", "Kaspi-дегі карточка")}</a>` : ""}${KASPI_REVIEW ? `<a href="${esc(KASPI_REVIEW)}" target="_blank" rel="noopener">${T("Оставить отзыв", "Пікір қалдыру")}</a>` : ""}</div>
  </div>
  <p class="copy">© ATARIA</p>
</footer>`;
  }

  function page({ url, title, desc, body, active = null, image, extraHead = "", bare = false }) {
    const full = title.includes("ATARIA") ? title : `${title} · ATARIA`;
    const og = image ? `${SITE}/${image}` : `${SITE}/img/m-hero.jpg`;
    emit(url, `<!doctype html>
<html lang="${lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>${esc(full)}</title>
<meta name="description" content="${esc(desc)}">
<meta property="og:title" content="${esc(full)}">
<meta property="og:description" content="${esc(desc)}">
<meta property="og:image" content="${esc(og)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="${kk ? "kk_KZ" : "ru_RU"}">
<meta name="theme-color" content="#17110E">
<link rel="canonical" href="${SITE}${P}${url}">
<link rel="alternate" hreflang="ru" href="${SITE}${url}">
<link rel="alternate" hreflang="kk" href="${SITE}/kk${url}">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="icon" href="/img/icon-192.png" type="image/png">
<link rel="apple-touch-icon" href="/img/icon-192.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&family=Unbounded:wght@300;400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
${extraHead}
<script>document.documentElement.classList.add("anim")</script>
</head>
<body class="${bare ? "choose" : ""}">
${bare ? "" : header(active, url)}
<main id="main">
${body}
</main>
${bare ? "" : footer()}
<script src="/motion.js" defer></script>
<script src="/site.js" defer></script>
<script src="/anim.js" defer></script>
</body>
</html>
`);
  }

  const crumbs = (list) => `<nav class="crumbs" aria-label="${T("Путь", "Жол")}">${list.map(([l, h]) => (h ? `<a href="${h}">${esc(l)}</a>` : `<span>${esc(l)}</span>`)).join("<i>/</i>")}</nav>`;
  const HOME = T("Главная", "Басты бет");

  function layout(p, active, inner, sideExtra = "") {
    const nav = productNav(p, active).map((x) => `<a href="${x.href}" class="${x.on ? "on" : ""}">${x.l}</a>`).join("");
    return `<div class="shell">
  <aside class="aside"><p class="eyebrow">${esc(p.name)}</p><nav>${nav}</nav>${sideExtra}</aside>
  <div class="content">
    <nav class="tabs" aria-label="${T("Разделы", "Бөлімдер")}">${nav}</nav>
    ${inner}
  </div>
</div>`;
  }

  const pageHead = (eyebrow, title, lead = "") => `<div class="page-head"><p class="eyebrow">${esc(eyebrow)}</p><h1>${esc(title)}</h1>${lead ? `<p class="lead">${esc(lead)}</p>` : ""}</div>`;

  const attGrid = (p, list) => `<div class="grid">${list.map((a) => `<a class="card att" href="${P}/${p.id}/attachments/${a.id}/">
    <div class="ph">${media(a)}</div>
    <div class="body"><span class="meta">${esc(a.group)}${a.speed ? ` · ${T("скорость", "жылдамдық")} ${esc(a.speed)}` : ""}</span><h3>${esc(a.name)}</h3><span class="meta">${esc(a.short)}</span></div></a>`).join("")}</div>`;

  const recGrid = (p, list) => `<div class="grid">${list.map((r) => `<a class="card" href="${P}/${p.id}/recipes/${r.id}/">
    <div class="ph">${r.image ? `<img src="/${esc(r.image)}" alt="${esc(r.title)}" loading="lazy">` : ""}<span class="time">${ICONS.clock}${esc(r.time)}</span></div>
    <div class="body"><span class="meta">${esc(r.tag)}</span><h3>${esc(r.title)}</h3>
      <div class="chips">${r.attachments.map((id) => `<span class="chip">${esc(att(p, id)?.name || id)}</span>`).join("")}</div></div></a>`).join("")}</div>`;

  function reviewBlock(p, big = false) {
    if (!KASPI_REVIEW) return "";
    return `<section class="block-section"><div class="review">
    <div><p class="eyebrow">${kk ? `${esc(p.name)} ұнай ма?` : `Вам нравится ${esc(p.name)}?`}</p>
    <h3>${big ? T("Оставьте отзыв на Kaspi, это займёт минуту", "Kaspi-де пікір қалдырыңыз, бұл бір минут алады") : T("Будем рады вашему отзыву на Kaspi", "Kaspi-дегі пікіріңізге қуанамыз")}</h3>
    <p class="lead sm">${T("Отзыв помогает другим выбрать, а нам становиться лучше.", "Пікір басқаларға таңдауға көмектеседі, ал бізге жақсара түсуге.")} ${esc(DATA.support.kaspi_review_hint || "")}</p></div>
    <a class="btn" href="${esc(KASPI_REVIEW)}" target="_blank" rel="noopener">${T("Оставить отзыв на Kaspi", "Kaspi-де пікір қалдыру")}</a>
  </div></section>`;
  }

  const helpBand = () => `<section class="block-section"><div class="band">
  <div><p class="eyebrow">${T("Помощь", "Көмек")}</p><h3>${T("Что-то не получается?", "Бірдеңе шықпай жатыр ма?")}</h3><p class="lead sm">${T("Напишите нам в WhatsApp. Подскажем по насадкам, скоростям и рецептам.", "WhatsApp-қа жазыңыз. Қондырмалар, жылдамдықтар және рецепттер бойынша кеңес береміз.")}</p></div>
  <a class="btn" href="${esc(WA)}" target="_blank" rel="noopener">${T("Написать в WhatsApp", "WhatsApp-қа жазу")}</a></div></section>`;

  const L = {
    start: T("С чего начать", "Қалай бастау керек"),
    recipes: T("Рецепты", "Рецепттер"),
    attachments: T("Насадки", "Қондырмалар"),
    speeds: T("Скорости", "Жылдамдықтар"),
    care: T("Уход", "Күтім"),
  };

  // ---------- Chooser (first screen) ----------
  page({
    url: "/",
    bare: true,
    title: T("ATARIA — выберите вашу технику", "ATARIA — техникаңызды таңдаңыз"),
    desc: T("Инструкции, насадки и рецепты для техники ATARIA: кухонная машина и аэрогриль.", "ATARIA техникасына арналған нұсқаулықтар, қондырмалар және рецепттер: асүй машинасы және аэрогриль."),
    image: "img/m-hero.jpg",
    body: `<div class="choose-top">
  <a href="${P}/" class="logo" aria-label="ATARIA"><img src="/img/logo.png" alt="ATARIA" width="96" height="66"></a>
  <div class="lang" role="group" aria-label="Тіл / Язык"><a href="/" class="${kk ? "" : "on"}" hreflang="ru" data-lang="ru">RU</a><a href="/kk/" class="${kk ? "on" : ""}" hreflang="kk" data-lang="kk">ҚАЗ</a></div>
</div>
<section class="split-screen" aria-label="${T("Выбор техники", "Техниканы таңдау")}">
  <a class="half" href="${P}/sm23/">
    <img src="/img/m-side.jpg" alt="${T("Кухонная машина ATARIA AT-SM23", "ATARIA AT-SM23 асүй машинасы")}">
    <div class="cap"><p class="eyebrow">${T("Кухонная машина", "Асүй машинасы")}</p><h2>AT-SM23</h2><p class="sub">${T("Насадки, скорости и 21 рецепт", "Қондырмалар, жылдамдықтар және 21 рецепт")}</p><span class="cta">${T("Открыть", "Ашу")} <i>→</i></span></div>
  </a>
  <a class="half soon" href="${P}/airfryer/">
    <img src="/img/af-hero.jpg" alt="${T("Аэрогриль ATARIA", "ATARIA аэрогрилі")}">
    <span class="badge">${T("Скоро", "Жақында")}</span>
    <div class="cap"><p class="eyebrow">${T("Аэрогриль", "Аэрогриль")}</p><h2>${T("Аэрогриль", "Аэрогриль")}</h2><p class="sub">${T("Режимы и рецепты готовим к выходу", "Режимдер мен рецепттерді шығаруға дайындап жатырмыз")}</p><span class="cta">${T("Узнать первым", "Бірінші болып білу")} <i>→</i></span></div>
  </a>
</section>`,
  });

  // ---------- Home ----------
  page({
    url: "/sm23/",
    active: "",
    image: "img/m-hero.jpg",
    title: T("ATARIA — рецепты и инструкции", "ATARIA — рецепттер мен нұсқаулықтар"),
    desc: T("Как пользоваться техникой ATARIA: насадки, скорости, пошаговые рецепты и уход.", "ATARIA техникасын қалай қолдану керек: қондырмалар, жылдамдықтар, қадамдық рецепттер және күтім."),
    body: `
<section class="hero">
  <div class="hero-txt">
    <p class="eyebrow">${T("Инструкция и рецепты · ATARIA AT-SM23", "Нұсқаулық және рецепттер · ATARIA AT-SM23")}</p>
    <h1>${T("Как готовить на вашей кухонной машине", "Асүй комбайнында қалай дайындау керек")}</h1>
    <p class="lead">${T("Какую насадку поставить, на какой скорости включать и что приготовить. Всё по шагам, с граммами и таймером.", "Қандай қондырма орнату керек, қай жылдамдықта қосу керек және не дайындауға болады. Бәрі қадамдап, грамммен және таймермен.")}</p>
    <button class="hero-search" id="hero-search" type="button">${ICONS.search}<span>${T("Например: тесто, фарш, взбить сливки", "Мысалы: қамыр, қайма, кілегей көпіршіту")}</span></button>
    <p class="eyebrow" style="margin-top:26px">${T("Что хотите сделать?", "Не істегіңіз келеді?")}</p>
    <div class="tasks">
      <a href="${P}/sm23/attachments/hook/">${T("Замесить тесто", "Қамыр илеу")} <i>→</i></a>
      <a href="${P}/sm23/attachments/grinder/">${T("Прокрутить фарш", "Қайма тарту")} <i>→</i></a>
      <a href="${P}/sm23/attachments/whisk/">${T("Взбить сливки или белки", "Кілегей немесе ақуыз көпіршіту")} <i>→</i></a>
      <a href="${P}/sm23/attachments/roller/">${T("Раскатать тесто", "Қамыр жаю")} <i>→</i></a>
      <a href="${P}/sm23/attachments/slicer/">${T("Натереть или нарезать овощи", "Көкөністі үгу немесе кесу")} <i>→</i></a>
      <a href="${P}/sm23/attachments/noodle/">${T("Нарезать лапшу", "Кеспе кесу")} <i>→</i></a>
    </div>
    <div class="actions"><a class="btn" href="${P}/sm23/start/">${T("Первый запуск за 5 шагов", "Алғашқы іске қосу — 5 қадам")}</a><a class="btn ghost" href="${P}/sm23/recipes/">${T("Все рецепты", "Барлық рецепттер")}</a></div>
  </div>
  <div class="hero-ph tall"><img src="/img/m-side.jpg" alt="${T("Кухонная машина ATARIA AT-SM23", "ATARIA AT-SM23 асүй машинасы")}"></div>
</section>

<section class="tech">
  <div class="wrap">
    <div class="tech-strip">
      <div><b>2000</b><span>${T("Вт мощность", "Вт қуат")}</span></div>
      <div><b>7</b><span>${T("литров чаша", "литр тостаған")}</span></div>
      <div><b>15</b><span>${T("минут таймер, шаг 30 с", "минут таймер, қадамы 30 с")}</span></div>
      <div><b>P·6</b><span>${T("импульс и 6 скоростей", "импульс және 6 жылдамдық")}</span></div>
    </div>
    ${[
      ["t-planet", T("Планетарное вращение", "Планеталық айналу"), T("Насадка вращается вокруг своей оси и одновременно обходит всю чашу. Тесто вымешивается равномерно, без комков у стенок.", "Қондырма өз осінен айналып, бір мезгілде бүкіл тостағанды айналып шығады. Қамыр қабырғаларда кесексіз біркелкі иленеді.")],
      ["t-bowl", T("Чаша 7 литров с крышкой", "Қақпағы бар 7 литрлік тостаған"), T("Стальная чаша вмещает тесто на большую семью. Прозрачная крышка не даёт муке разлетаться, а через носик удобно добавлять продукты на ходу.", "Болат тостағанға үлкен отбасына жететін қамыр сыяды. Мөлдір қақпақ ұнды шашыратпайды, ал шүмек арқылы өнімді жұмыс кезінде қосуға ыңғайлы.")],
      ["t-power", T("Мотор 2000 Вт", "2000 Вт мотор"), T("Мощности хватает на тугое тесто для беша, мантов и лапши. Машина работает уверенно, не перегреваясь на долгом замесе.", "Қуаты бесбармаққа, мантыға және кеспеге арналған қатты қамырға жетеді. Ұзақ илеуде қызып кетпей, сенімді жұмыс істейді.")],
      ["t-timer", T("Таймер до 15 минут", "15 минутқа дейін таймер"), T("Задайте время кнопками TIME, + и − с шагом 30 секунд. По окончании машина сама остановится, можно не стоять рядом.", "TIME, + және − түймелерімен уақытты 30 секунд қадаммен орнатыңыз. Уақыт біткенде машина өзі тоқтайды, қасында тұрудың қажеті жоқ.")],
      ["t-speed", T("Импульс и 6 скоростей", "Импульс және 6 жылдамдық"), T("Ноль сверху, справа скорости от 1 до 6, слева импульс P. Крюку хватает 1–2, венчик и лопатка работают на всех скоростях.", "Нөл жоғарыда, оң жақта 1-ден 6-ға дейінгі жылдамдықтар, сол жақта P импульсі. Ілгекке 1–2 жеткілікті, венчик пен көрекше барлық жылдамдықта жұмыс істейді.")],
      ["t-port", T("Боковой разъём под насадки", "Қондырмаларға арналған бүйір ұяшық"), T("Поднимите крышку с треугольником и подключите мясорубку, овощерезку, тестораскатку или лапшерезку. Одна машина вместо шести приборов.", "Үшбұрышты қақпақты көтеріп, ет тартқышты, көкөніс турағышты, қамыр жаятын немесе кеспе турағыш қондырманы қосыңыз. Алты құралдың орнына бір машина.")],
    ].map(([img, h, t], i) => `<article class="feat"><figure><img src="/img/${img}.jpg" alt="${esc(h)}" loading="lazy"></figure><div class="txt"><p class="eyebrow">${String(i + 1).padStart(2, "0")}</p><h3>${esc(h)}</h3><p>${esc(t)}</p></div></article>`).join("")}
    <div class="actions center"><a class="btn" href="${P}/sm23/attachments/">${T("Все насадки", "Барлық қондырмалар")}</a><a class="btn ghost" href="${P}/sm23/about/">${T("Характеристики", "Сипаттамалар")}</a></div>
  </div>
</section>

<section class="wrap block-section">
  <div class="sec-head"><h2>${T("Что можно приготовить", "Не дайындауға болады")}</h2></div>
  <div class="scenes">
    <a class="scene-card big" href="${P}/sm23/attachments/hook/"><img src="/img/a-hook.jpg" alt="" loading="lazy"><span><b>${T("Тесто", "Қамыр")}</b>${T("Крюк, скорость 1–2", "Ілгек, 1–2 жылдамдық")}</span></a>
    <a class="scene-card" href="${P}/sm23/attachments/whisk/"><img src="/img/a-whisk.jpg" alt="" loading="lazy"><span><b>${T("Крем и безе", "Крем және безе")}</b>${T("Венчик, скорость 1–6", "Венчик, 1–6 жылдамдық")}</span></a>
    <a class="scene-card" href="${P}/sm23/attachments/roller/"><img src="/img/a-roller.jpg" alt="" loading="lazy"><span><b>${T("Раскатка и лапша", "Қамыр жаю және кеспе")}</b>${T("8 уровней толщины", "8 қалыңдық деңгейі")}</span></a>
    <a class="scene-card" href="${P}/sm23/attachments/slicer/"><img src="/img/a-slicer.jpg" alt="" loading="lazy"><span><b>${T("Овощи и сыр", "Көкөніс және ірімшік")}</b>${T("Три барабана", "Үш барабан")}</span></a>
    <a class="scene-card" href="${P}/sm23/attachments/grinder/"><img src="/img/a-grinder.jpg" alt="" loading="lazy"><span><b>${T("Фарш", "Қайма")}</b>${T("Мясорубка, скорость 1–6", "Ет тартқыш, 1–6 жылдамдық")}</span></a>
  </div>
</section>

<section class="wrap block-section">
  <div class="sec-head"><h2>${T("Что приготовить сегодня", "Бүгін не дайындаймыз")}</h2><a href="${P}/sm23/recipes/">${T("Все рецепты →", "Барлық рецепттер →")}</a></div>
  ${recGrid(sm, sm.recipes.slice(0, 4))}
</section>

<section class="wrap block-section">
  <div class="sec-head"><h2>${T("Всё о вашей машине", "Машинаңыз туралы бәрі")}</h2></div>
  <div class="tiles">
    <a href="${P}/sm23/start/"><span class="ic">${ICONS.book}</span><h3>${L.start}</h3><p>${T("Пять шагов до первого замеса.", "Алғашқы илеуге дейін бес қадам.")}</p></a>
    <a href="${P}/sm23/attachments/"><span class="ic">${ICONS.parts}</span><h3>${L.attachments}</h3><p>${T("Для чего каждая и как ею пользоваться.", "Әрқайсысы не үшін және қалай қолданылады.")}</p></a>
    <a href="${P}/sm23/speeds/"><span class="ic">${ICONS.speed}</span><h3>${L.speeds}</h3><p>${T("Какую выбрать для теста, крема и фарша.", "Қамырға, кремге және қаймаға қайсысын таңдау керек.")}</p></a>
    <a href="${P}/sm23/care/"><span class="ic">${ICONS.care}</span><h3>${L.care}</h3><p>${T("Как мыть и хранить, чтобы служила годами.", "Жылдар бойы қызмет ету үшін қалай жуу және сақтау керек.")}</p></a>
  </div>
</section>
<div class="wrap">${helpBand()}</div>`,
  });

  // ---------- Product overview ----------
  page({
    url: "/sm23/about/",
    title: `${sm.name}: ${T("инструкция и рецепты", "нұсқаулық және рецепттер")}`,
    desc: sm.intro,
    image: sm.hero,
    active: "about",
    body: `
<section class="p-hero wrap">
  <div class="txt">
    ${crumbs([[HOME, `${P}/sm23/`], [sm.kind, ""]])}
    <p class="eyebrow">${esc(sm.kind)}</p>
    <h1>${esc(sm.name)}</h1>
    <div class="rule"></div>
    <p class="lead">${esc(sm.intro)}</p>
    <div class="actions"><a class="btn" href="${P}/sm23/start/">${L.start}</a><a class="btn ghost" href="${P}/sm23/recipes/">${L.recipes}</a></div>
  </div>
  <div class="ph"><img src="/${esc(sm.hero)}" alt="${esc(sm.name)}"></div>
</section>
<div class="wrap">
  <div class="specs">${sm.specs.map((s) => `<div class="spec"><div class="k">${esc(s.label)}</div><div class="v">${esc(s.value)}</div></div>`).join("")}</div>

  <div class="tiles block-section">
    <a href="${P}/sm23/start/"><span class="ic">${ICONS.book}</span><h3>${L.start}</h3><p>${T("Первый запуск за 5 шагов.", "Алғашқы іске қосу 5 қадамда.")}</p></a>
    <a href="${P}/sm23/attachments/"><span class="ic">${ICONS.parts}</span><h3>${L.attachments}</h3><p>${T(`${sm.attachments.length} насадок и для чего они.`, `${sm.attachments.length} қондырма және олар не үшін.`)}</p></a>
    <a href="${P}/sm23/recipes/"><span class="ic">${ICONS.book}</span><h3>${L.recipes}</h3><p>${T(`${sm.recipes.length} проверенных рецептов.`, `${sm.recipes.length} сыналған рецепт.`)}</p></a>
    <a href="${P}/sm23/care/"><span class="ic">${ICONS.care}</span><h3>${L.care}</h3><p>${T("Мытьё, хранение, безопасность.", "Жуу, сақтау, қауіпсіздік.")}</p></a>
  </div>

  <div class="story">
    <div class="ph"><img src="/img/sm23-host.jpg" alt="${T("Хозяйка засыпает муку в чашу ATARIA", "Үй иесі ATARIA тостағанына ұн салып жатыр")}" loading="lazy"></div>
    <div class="txt">
      <p class="eyebrow">${T("Как это бывает дома", "Үйде былай болады")}</p>
      <blockquote>${T("«Засыпала муку, нажала кнопку и пошла резать лук. Через три минуты тесто для беша готово, руки чистые»", "«Ұнды салып, түймені басып, пиязды турауға кеттім. Үш минуттан кейін бесбармаққа қамыр дайын, қолым таза»")}</blockquote>
      <p class="lead sm">${T("Машина берёт на себя самое тяжёлое: замес, фарш, раскатку. Вам остаётся самое приятное.", "Машина ең ауыр жұмысты өзіне алады: илеу, қайма, жаю. Сізге ең жағымдысы қалады.")}</p>
      <div class="actions"><a class="btn ghost" href="${P}/sm23/recipes/besh/">${T("Рецепт теста для беша", "Бесбармаққа қамыр рецепті")}</a></div>
    </div>
  </div>

  <section class="block-section">
    <div class="sec-head"><h2>${L.attachments}</h2><a href="${P}/sm23/attachments/">${T("Все насадки →", "Барлық қондырмалар →")}</a></div>
    ${attGrid(sm, sm.attachments.slice(0, 4))}
  </section>
  <section class="block-section">
    <div class="sec-head"><h2>${T("Что приготовить", "Не дайындаймыз")}</h2><a href="${P}/sm23/recipes/">${T("Все рецепты →", "Барлық рецепттер →")}</a></div>
    ${recGrid(sm, sm.recipes.slice(0, 4))}
  </section>
  ${helpBand()}
</div>`,
  });

  // ---------- Start ----------
  page({
    url: "/sm23/start/",
    title: L.start,
    desc: T("Первый запуск кухонной машины ATARIA AT-SM23 за пять простых шагов.", "ATARIA AT-SM23 асүй комбайнын бес қарапайым қадамда алғаш рет іске қосу."),
    active: "start",
    body: `<div class="wrap">${crumbs([[HOME, `${P}/sm23/`], [sm.kind, `${P}/sm23/`], [L.start, ""]])}${layout(sm, "start", `
    ${pageHead(T("Первый запуск", "Алғашқы іске қосу"), L.start, T("Пять шагов, и вы готовы к первому замесу.", "Бес қадам, сонда алғашқы илеуге дайынсыз."))}
    <div class="steps">${sm.quickstart.map((s, i) => `<div class="step"><div class="n">${i + 1}</div><div><h3>${esc(s.title)}</h3><p>${esc(s.text)}</p></div></div>`).join("")}</div>
    <section class="block-section"><div class="sec-head"><h2>${T("Что где на машине", "Машинада не қайда")}</h2></div>
      <div class="split"><div class="ph"><img src="/img/controls.jpg" alt="${T("Дисплей с таймером, рычаг и регулятор скорости", "Таймері бар дисплей, тетік және жылдамдық реттегіші")}" loading="lazy"></div>
      <div class="parts one">${sm.parts.map((x) => `<div class="part"><h3>${esc(x.name)}</h3><p>${esc(x.text)}</p></div>`).join("")}</div></div>
    </section>
    <div class="actions"><a class="btn" href="${P}/sm23/attachments/">${T("Дальше: насадки", "Әрі қарай: қондырмалар")}</a><a class="btn ghost" href="${P}/sm23/speeds/">${L.speeds}</a></div>`)}</div>`,
  });

  // ---------- Speeds ----------
  page({
    url: "/sm23/speeds/",
    title: T("Какая скорость для чего", "Қай жылдамдық не үшін"),
    desc: T("Таблица скоростей кухонной машины ATARIA AT-SM23 для теста, крема, фарша и овощей.", "ATARIA AT-SM23 комбайнының қамыр, крем, қайма және көкөніске арналған жылдамдық кестесі."),
    active: "speeds",
    body: `<div class="wrap">${crumbs([[HOME, `${P}/sm23/`], [sm.kind, `${P}/sm23/`], [L.speeds, ""]])}${layout(sm, "speeds", `
    ${pageHead(T("Подсказка", "Кеңес"), T("Какая скорость для чего", "Қай жылдамдық не үшін"), T("Всегда начинайте со скорости 1 и прибавляйте постепенно. Так мука не разлетится по кухне.", "Әрдайым 1-жылдамдықтан бастап, біртіндеп арттырыңыз. Сонда ұн асүйге шашылмайды."))}
    <div class="speeds">${sm.speeds.map((s) => `<a href="${P}/sm23/attachments/${s.attachment}/"><span class="nm">${esc(s.name)}</span><span class="rg">${esc(s.range)}</span><span class="fo">${esc(s.for)}</span></a>`).join("")}</div>
    <div class="split dialrow"><div class="ph"><img src="/img/dial-real.jpg" alt="${T("Регулятор скорости: метки P, 0, 1–6", "Жылдамдық реттегіші: P, 0, 1–6 белгілері")}" loading="lazy"></div>
    <div class="parts one"><div class="part"><h3>${T("Как читать регулятор", "Реттегішті қалай оқу керек")}</h3><p>${T("Ромбик на ручке показывает выбранный режим. Ноль сверху, это выключено. Скорости 1–6 идут вправо по часовой стрелке. Слева от нуля стоит P: импульс, пока вы держите ручку.", "Тұтқадағы ромб таңдалған режимді көрсетеді. Нөл жоғарыда, бұл өшірулі. 1–6 жылдамдықтары сағат тілімен оңға қарай жүреді. Нөлдің сол жағында P тұр: тұтқаны ұстап тұрғанда ғана импульс.")}</p></div></div></div>
    <div class="note"><b>${T("Режим P.", "P режимі.")}</b> ${T("Импульсный режим работает, пока вы держите кнопку. Подходит, чтобы быстро измельчить или перемешать.", "Импульстік режим түймені басып тұрғанша жұмыс істейді. Тез ұсақтауға немесе араластыруға жарайды.")}</div>
    ${helpBand()}`)}</div>`,
  });

  // ---------- Attachments ----------
  {
    const groups = [...new Set(sm.attachments.map((a) => a.group))];
    page({
      url: "/sm23/attachments/",
      title: L.attachments,
      desc: T("Все насадки ATARIA AT-SM23: крюк, лопатка, венчик, мясорубка, овощерезка, блендер, тестораскатка и лапшерезка.", "ATARIA AT-SM23 барлық қондырмалары: ілгек, көрекше, венчик, ет тартқыш, көкөніс турағыш, блендер, қамыр жаятын қондырма және кеспе турағыш."),
      active: "attachments",
      body: `<div class="wrap">${crumbs([[HOME, `${P}/sm23/`], [sm.kind, `${P}/sm23/`], [L.attachments, ""]])}${layout(sm, "attachments", `
      ${pageHead(sm.name, L.attachments, T("В чаше месим и взбиваем. Сбоку крутим, трём, раскатываем и режем. Сверху блендер.", "Тостағанда илейміз және көпіршітеміз. Бүйір жағында тартамыз, үгеміз, жаямыз және кесеміз. Үстінде — блендер."))}
      ${groups.map((g) => `<section class="grp"><p class="eyebrow">${esc(g)}</p>${attGrid(sm, sm.attachments.filter((a) => a.group === g))}</section>`).join("")}`)}</div>`,
    });
    for (const a of sm.attachments) {
      const recs = sm.recipes.filter((r) => r.attachments.includes(a.id));
      const side = `<p class="eyebrow" style="margin-top:26px">${T("Все насадки", "Барлық қондырмалар")}</p><nav>${sm.attachments.map((x) => `<a href="${P}/sm23/attachments/${x.id}/" class="${x.id === a.id ? "on" : ""}">${esc(x.name)}</a>`).join("")}</nav>`;
      page({
        url: `/sm23/attachments/${a.id}/`,
        title: a.name,
        desc: a.what,
        image: a.image,
        active: "attachments",
        body: `<div class="wrap">${crumbs([[HOME, `${P}/sm23/`], [sm.kind, `${P}/sm23/`], [L.attachments, `${P}/sm23/attachments/`], [a.name, ""]])}${layout(sm, "attachments", `
        <div class="split top">
          <div class="sticky-col"><div class="ph sticky">${media(a)}<span class="cap-t">${String(sm.attachments.indexOf(a) + 1).padStart(2, "0")} · ${esc(a.name)}</span>${a.speed ? `<span class="cap-b">${T("Скорость", "Жылдамдық")} ${esc(a.speed)}</span>` : ""}</div></div>
          <div>
            <p class="eyebrow">${esc(a.group)}</p><h1>${esc(a.name)}</h1><div class="rule"></div>
            <p class="lead">${esc(a.what)}</p>
            ${a.speed ? `<div class="speedbig"><span class="eyebrow">${T("Скорость", "Жылдамдық")}</span><b>${esc(a.speed)}</b></div>` : ""}
            <div class="block"><h3>${T("Подходит для", "Не үшін жарайды")}</h3><div class="chips">${a.use_for.map((u) => `<span class="chip">${esc(u)}</span>`).join("")}</div></div>
            ${a.kit ? `<div class="block"><h3>${T("В комплекте", "Жинақта")}</h3><ul class="clean">${a.kit.map((k) => `<li>${esc(k)}</li>`).join("")}</ul></div>` : ""}
            <div class="block"><h3>${T("Как пользоваться", "Қалай қолдану керек")}</h3><ol class="num">${a.how.map((k) => `<li>${esc(k)}</li>`).join("")}</ol></div>
            <div class="block"><h3>${T("Совет", "Кеңес")}</h3><ul class="clean">${a.tips.map((k) => `<li>${esc(k)}</li>`).join("")}</ul></div>
            <div class="block"><h3>${T("Чего не делать", "Не істеуге болмайды")}</h3><ul class="clean warn">${a.dont.map((k) => `<li>${esc(k)}</li>`).join("")}</ul></div>
          </div>
        </div>
        ${recs.length ? `<section class="block-section"><div class="sec-head"><h2>${T("Рецепты с этой насадкой", "Осы қондырмасы бар рецепттер")}</h2></div>${recGrid(sm, recs)}</section>` : ""}`, side)}</div>`,
      });
    }
  }

  // ---------- Recipes ----------
  {
    const ALL = T("Все", "Барлығы");
    const tags = [ALL, ...new Set(sm.recipes.map((r) => r.tag))];
    page({
      url: "/sm23/recipes/",
      title: L.recipes,
      desc: T("Проверенные рецепты для ATARIA AT-SM23 с точными граммами, скоростями и временем.", "ATARIA AT-SM23 үшін нақты граммдары, жылдамдығы және уақыты бар сыналған рецепттер."),
      active: "recipes",
      body: `<div class="wrap">${crumbs([[HOME, `${P}/sm23/`], [sm.kind, `${P}/sm23/`], [L.recipes, ""]])}${layout(sm, "recipes", `
      ${pageHead(sm.name, L.recipes, T("Точные граммы, скорости и время. Откройте рецепт и нажмите «Готовить по шагам»: крупный текст и таймер прямо в телефоне.", "Нақты граммдар, жылдамдықтар және уақыт. Рецептті ашып, «Қадамдап дайындау» түймесін басыңыз: ірі мәтін және таймер телефоныңызда."))}
      <div class="filters" id="filters">${tags.map((t, i) => `<button data-tag="${esc(t)}" data-all="${i === 0 ? 1 : 0}" class="${i === 0 ? "on" : ""}">${esc(t)}</button>`).join("")}</div>
      <div class="grid" id="rgrid">${sm.recipes.map((r) => `<a class="card" data-tag="${esc(r.tag)}" href="${P}/sm23/recipes/${r.id}/">
        <div class="ph"><img src="/${esc(r.image)}" alt="${esc(r.title)}" loading="lazy"><span class="time">${ICONS.clock}${esc(r.time)}</span></div>
        <div class="body"><span class="meta">${esc(r.tag)} · ${esc(r.servings)}</span><h3>${esc(r.title)}</h3>
        <div class="chips">${r.attachments.map((id) => `<span class="chip">${esc(att(sm, id)?.name || id)}</span>`).join("")}</div></div></a>`).join("")}</div>`)}</div>`,
    });
    sm.recipes.forEach((r, idx) => {
      const others = sm.recipes.filter((x) => x.id !== r.id);
      const side = `<p class="eyebrow" style="margin-top:26px">${T("Все рецепты", "Барлық рецепттер")}</p><nav>${sm.recipes.map((x) => `<a href="${P}/sm23/recipes/${x.id}/" class="${x.id === r.id ? "on" : ""}">${esc(x.title)}</a>`).join("")}</nav>`;
      const ld = { "@context": "https://schema.org", "@type": "Recipe", name: r.title, image: `${SITE}/${r.image}`, description: r.intro, inLanguage: lang,
        recipeYield: r.servings, recipeIngredient: r.ingredients, recipeInstructions: r.steps.map((s) => ({ "@type": "HowToStep", text: s.text })) };
      const labels = { step: T("шаг", "қадам"), of: T("из", "/"), close: T("Закрыть", "Жабу"), start: T("Запустить таймер", "Таймерді қосу"), pause: T("Пауза", "Кідірту"), back: T("Назад", "Артқа"), next: T("Дальше", "Әрі қарай"), done: T("Готово", "Дайын"), speed: T("скорость", "жылдамдық"), alarm: T("Время вышло!", "Уақыт бітті!"), stopSound: T("Выключить сигнал", "Дыбысты өшіру"), notifyTitle: T("Таймер ATARIA", "ATARIA таймері"), notifyBody: T("Время вышло — загляните на кухню", "Уақыт бітті — асүйге қараңыз"), resume: T("Таймер идёт", "Таймер жүріп жатыр") };
      page({
        url: `/sm23/recipes/${r.id}/`,
        title: r.title,
        desc: r.intro,
        image: r.image,
        active: "recipes",
        extraHead: `<script type="application/ld+json">${JSON.stringify(ld)}</script>`,
        body: `<div class="wrap">${crumbs([[HOME, `${P}/sm23/`], [sm.kind, `${P}/sm23/`], [L.recipes, `${P}/sm23/recipes/`], [r.title, ""]])}${layout(sm, "recipes", `
        <div class="cover"><img src="/${esc(r.image)}" alt="${esc(r.title)}"></div>
        <div class="page-head tight"><p class="eyebrow">${esc(r.tag)}</p><h1>${esc(r.title)}</h1><p class="lead">${esc(r.intro)}</p></div>
        <div class="meta-strip">
          <div>${ICONS.clock}<span><b>${esc(r.time)}</b>${T("время", "уақыты")}</span></div>
          <div>${ICONS.people}<span><b id="yield">${esc(r.servings)}</b>${T("порций", "порция")}</span></div>
          <div>${ICONS.parts}<span><b>${r.attachments.map((id) => esc(att(sm, id)?.name || id)).join(", ")}</b>${T("насадки", "қондырмалар")}</span></div>
        </div>
        <div class="actions"><button class="btn" id="cook">${T("Готовить по шагам", "Қадамдап дайындау")}</button>
          ${r.attachments.map((id) => `<a class="btn ghost" href="${P}/sm23/attachments/${id}/">${esc(att(sm, id)?.name || id)}</a>`).join("")}</div>
        <div class="recipe-cols">
          <div class="ing-box" id="ingbox" data-base="${r.base || 4}" data-yield="${esc(r.servings)}" data-scale-yield="${r.scaleYield ? 1 : 0}" data-note="${r.attachments.some((a) => ["hook", "whisk"].includes(a)) ? esc(T("Большую порцию готовьте партиями: чаша рассчитана на 7 л, не перегружайте машину.", "Үлкен порцияны бөліп дайындаңыз: тостаған 7 л-ге арналған, машинаны артық жүктемеңіз.")) : ""}" data-people="${esc(T("На {n} чел.", "{n} адамға"))}"><h3>${T("Что понадобится", "Не қажет")}</h3>
            <p class="people-q">${T("На сколько человек готовим?", "Неше адамға дайындаймыз?")}</p>
            <div class="people" id="people" role="group">
              <button type="button" data-n="2"><b>1–2</b><span>${T("одному", "жалғыз")}</span></button>
              <button type="button" data-n="4"><b>3–4</b><span>${T("семье", "отбасы")}</span></button>
              <button type="button" data-n="6"><b>5–6</b><span>${T("большой семье", "үлкен отбасы")}</span></button>
              <button type="button" data-n="12"><b>10+</b><span>${T("друзьям", "достар")}</span></button>
            </div>
            <table class="ing">${r.ingredients.map((i) => { const [n, q] = splitIng(i); return `<tr><td>${esc(n)}</td><td data-q="${esc(q)}">${esc(q)}</td></tr>`; }).join("")}</table>
            <p class="scale-note" id="scale-note" hidden></p>
          </div>
          <div><h3 class="h-s">${T("Как готовить", "Қалай дайындау керек")}</h3><div class="rsteps">${r.steps.map((s, i) => `<div class="rstep"><div class="n">${i + 1}</div><div><p>${esc(s.text)}</p><div class="tags">
            ${s.attachment ? `<span class="chip">${esc(att(sm, s.attachment)?.name || "")}</span>` : ""}
            ${s.speed ? `<span class="chip">${T("скорость", "жылдамдық")} ${esc(s.speed)}</span>` : ""}
            ${s.minutes ? `<span class="chip">${esc(minutesLabel(s.minutes))}</span>` : ""}</div></div></div>`).join("")}</div></div>
        </div>
        ${reviewBlock(sm)}
        <section class="block-section"><div class="sec-head"><h2>${T("Ещё рецепты", "Тағы рецепттер")}</h2><a href="${P}/sm23/recipes/">${T("Все →", "Барлығы →")}</a></div>${recGrid(sm, [...others.slice(idx), ...others.slice(0, idx)].slice(0, 3))}</section>
        <script type="application/json" id="recipe-data">${JSON.stringify({ id: r.id, title: r.title, doneUrl: `${P}/sm23/recipes/${r.id}/done/`, labels, steps: r.steps.map((s) => ({ ...s, attachmentName: s.attachment ? att(sm, s.attachment)?.name : "" })) })}</script>`, side)}</div>`,
      });
      page({
        url: `/sm23/recipes/${r.id}/done/`,
        title: `${r.title}: ${T("готово", "дайын")}`,
        desc: T("Приятного аппетита!", "Ас болсын!"),
        image: r.image,
        active: "recipes",
        body: `<section class="done wrap">
        <p class="eyebrow">${esc(r.title)}</p><h1>${T("Приятного аппетита!", "Ас болсын!")}</h1><p class="lead">${T("Надеемся, получилось вкусно.", "Дәмді болды деп үміттенеміз.")}</p>
      </section>
      <div class="wrap">${reviewBlock(sm, true)}
      <section class="block-section"><div class="sec-head"><h2>${T("Что приготовить ещё", "Тағы не дайындаймыз")}</h2></div>${recGrid(sm, others.slice(0, 4))}</section></div>`,
      });
    });
  }

  // ---------- Care ----------
  page({
    url: "/sm23/care/",
    title: T("Уход и безопасность", "Күтім және қауіпсіздік"),
    desc: T("Как мыть, хранить и безопасно пользоваться кухонной машиной ATARIA AT-SM23.", "ATARIA AT-SM23 асүй комбайнын қалай жуу, сақтау және қауіпсіз қолдану керек."),
    active: "care",
    body: `<div class="wrap">${crumbs([[HOME, `${P}/sm23/`], [sm.kind, `${P}/sm23/`], [L.care, ""]])}${layout(sm, "care", `
    ${pageHead(sm.name, T("Уход и безопасность", "Күтім және қауіпсіздік"), T("Несколько простых привычек, и машина прослужит долгие годы.", "Бірнеше қарапайым әдет, сонда машина жылдар бойы қызмет етеді."))}
    <div class="parts">${sm.care.map((c) => `<div class="part"><h3>${esc(c.title)}</h3><p>${esc(c.text)}</p></div>`).join("")}</div>
    <section class="block-section"><div class="sec-head"><h2>${T("Важно", "Маңызды")}</h2></div><div class="note warnbox"><ul class="clean warn">${sm.safety.map((s) => `<li>${esc(s)}</li>`).join("")}</ul></div></section>`)}</div>`,
  });

  // ---------- Help ----------
  page({
    url: "/sm23/help/",
    title: T("Вопросы и помощь", "Сұрақтар және көмек"),
    desc: T("Ответы на частые вопросы по ATARIA AT-SM23 и связь с поддержкой.", "ATARIA AT-SM23 бойынша жиі қойылатын сұрақтарға жауаптар және қолдау қызметімен байланыс."),
    active: "help",
    extraHead: `<script type="application/ld+json">${JSON.stringify({ "@context": "https://schema.org", "@type": "FAQPage", inLanguage: lang, mainEntity: sm.faq.map((f) => ({ "@type": "Question", name: f.q, acceptedAnswer: { "@type": "Answer", text: f.a } })) })}</script>`,
    body: `<div class="wrap">${crumbs([[HOME, `${P}/sm23/`], [sm.kind, `${P}/sm23/`], [T("Помощь", "Көмек"), ""]])}${layout(sm, "help", `
    ${pageHead(sm.name, T("Вопросы и помощь", "Сұрақтар және көмек"))}
    <div class="faqs">${sm.faq.map((f) => `<details class="faq"><summary>${esc(f.q)}</summary><p>${esc(f.a)}</p></details>`).join("")}</div>
    ${helpBand()}${reviewBlock(sm)}`)}</div>`,
  });

  // ---------- Air fryer (soon) ----------
  page({
    url: "/airfryer/",
    title: T("Аэрогриль ATARIA — скоро", "ATARIA аэрогрилі — жақында"),
    desc: T("Инструкции и рецепты для аэрогриля ATARIA готовим к выходу.", "ATARIA аэрогриліне арналған нұсқаулықтар мен рецепттерді дайындап жатырмыз."),
    body: `<section class="hero soonp">
    <div class="hero-txt"><p class="eyebrow">${T("Скоро", "Жақында")}</p><h1>${esc(af.name)}</h1><div class="rule"></div>
      <p class="lead">${T("Здесь появятся инструкции, режимы и рецепты. Напишите нам, и мы сообщим, когда всё будет готово.", "Мұнда нұсқаулықтар, режимдер және рецепттер пайда болады. Бізге жазыңыз, бәрі дайын болғанда хабарлаймыз.")}</p>
      <div class="actions"><a class="btn" href="${esc(WA)}" target="_blank" rel="noopener">${T("Сообщить мне", "Маған хабарлаңыз")}</a><a class="btn ghost" href="${P}/sm23/">${T("К кухонной машине", "Асүй комбайнына")}</a></div></div>
    <div class="hero-ph"><img src="/img/af-hero.jpg" alt="${esc(af.name)}"></div></section>`,
  });

  // ---------- Search ----------
  page({
    url: "/search/",
    title: T("Поиск", "Іздеу"),
    desc: T("Поиск по инструкциям и рецептам ATARIA.", "ATARIA нұсқаулықтары мен рецепттерінен іздеу."),
    body: `<div class="wrap"><div class="page-head"><p class="eyebrow">${T("Поиск", "Іздеу")}</p><h1>${T("Найти на сайте", "Сайттан табу")}</h1></div>
    <div class="search-bar big" id="search2" data-empty="${T("Ничего не нашли. Напишите нам в WhatsApp, подскажем.", "Ештеңе табылмады. WhatsApp-қа жазыңыз, көмектесеміз.")}">${ICONS.search}<input id="q2" type="search" placeholder="${T("Например: тесто, мясорубка, скорость", "Мысалы: қамыр, ет тартқыш, жылдамдық")}" autocomplete="off"></div>
    <div id="results2" class="results"></div></div>`,
  });

  const index = [
    ...sm.recipes.map((r) => ({ t: r.title, u: `${P}/sm23/recipes/${r.id}/`, k: T("Рецепт", "Рецепт"), x: [r.intro, r.tag, ...r.ingredients].join(" ") })),
    ...sm.attachments.map((a) => ({ t: a.name, u: `${P}/sm23/attachments/${a.id}/`, k: T("Насадка", "Қондырма"), x: [a.what, a.short, ...a.use_for].join(" ") })),
    ...sm.faq.map((f) => ({ t: f.q, u: `${P}/sm23/help/`, k: T("Вопрос", "Сұрақ"), x: f.a })),
    { t: T("Какая скорость для чего", "Қай жылдамдық не үшін"), u: `${P}/sm23/speeds/`, k: T("Раздел", "Бөлім"), x: sm.speeds.map((s) => s.name + " " + s.for).join(" ") },
    { t: L.start, u: `${P}/sm23/start/`, k: T("Раздел", "Бөлім"), x: sm.quickstart.map((s) => s.title + " " + s.text).join(" ") },
    { t: T("Уход и безопасность", "Күтім және қауіпсіздік"), u: `${P}/sm23/care/`, k: T("Раздел", "Бөлім"), x: [...sm.care.map((c) => c.title + " " + c.text), ...sm.safety].join(" ") },
  ];
  fs.writeFileSync(path.join(ROOT, kk ? "search-index-kk.json" : "search-index.json"), JSON.stringify(index));
}

buildSite("ru");
buildSite("kk");

files.set("404.html", `<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>404 · ATARIA</title><link rel="stylesheet" href="/style.css"></head><body><section class="done wrap"><p class="eyebrow">404</p><h1>Такой страницы нет</h1><p class="lead">Возможно, ссылка устарела. / Бұл бет жоқ.</p><div class="actions" style="justify-content:center"><a class="btn" href="/">На главную</a><a class="btn ghost" href="/kk/">Басты бет</a></div></section></body></html>`);

// cache-busting: every /img/ file gets ?v=<content hash>, so a replaced photo never shows up stale
const crypto = await import("node:crypto");
const imgHash = new Map();
const withVersion = (html) => html.replace(/\/img\/([\w.-]+\.(?:jpg|png|webp))(?![\w?])/g, (m, name) => {
  if (!imgHash.has(name)) {
    const f = path.join(ROOT, "img", name);
    imgHash.set(name, fs.existsSync(f) ? crypto.createHash("md5").update(fs.readFileSync(f)).digest("hex").slice(0, 8) : "");
  }
  const h = imgHash.get(name);
  return h ? `${m}?v=${h}` : m;
});
for (const [rel, html] of files) {
  const out = path.join(ROOT, rel);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, withVersion(html));
}
const sitemap = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${pageUrls.map((u) => `<url><loc>${SITE}${u}</loc></url>`).join("\n")}\n</urlset>\n`;
fs.writeFileSync(path.join(ROOT, "sitemap.xml"), sitemap);
fs.writeFileSync(path.join(ROOT, "robots.txt"), `User-agent: *\nAllow: /\nSitemap: ${SITE}/sitemap.xml\n`);
console.log(`built ${files.size} pages`);
