// ATARIA guide: all text and data live in content.json so the future mobile app can reuse them as is.
const API = "https://jarvis-backend-alisher25.vercel.app";
const app = document.getElementById("app");
const topnav = document.getElementById("topnav");
let DATA = null;

const ICONS = {
  slicer: '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.3"><rect x="10" y="20" width="44" height="26" rx="13"/><circle cx="22" cy="33" r="1.4"/><circle cx="30" cy="29" r="1.4"/><circle cx="38" cy="33" r="1.4"/><circle cx="46" cy="29" r="1.4"/><circle cx="26" cy="38" r="1.4"/><circle cx="34" cy="38" r="1.4"/><circle cx="42" cy="38" r="1.4"/><path d="M6 33h4M54 33h4"/></svg>',
  roller: '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.3"><rect x="12" y="16" width="40" height="12" rx="6"/><rect x="12" y="30" width="40" height="12" rx="6"/><path d="M18 50c6-3 22-3 28 0M6 22h6M52 36h6"/></svg>',
  noodle: '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.3"><rect x="10" y="12" width="44" height="14" rx="7"/><path d="M18 30c0 10 2 18 0 24M26 30c0 10-2 18 0 24M34 30c0 10 2 18 0 24M42 30c0 10-2 18 0 24"/></svg>',
  airfryer: '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.2"><rect x="14" y="8" width="36" height="48" rx="14"/><rect x="20" y="30" width="24" height="18" rx="5"/><circle cx="32" cy="19" r="4"/><path d="M28 56v2M36 56v2"/></svg>',
};

const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const product = (id) => DATA.products.find((p) => p.id === id);
const att = (p, id) => p.attachments.find((a) => a.id === id);
const media = (item) => (item.image ? `<img src="${esc(item.image)}" alt="${esc(item.name || item.title)}" loading="lazy">` : ICONS[item.id] || "");
const waLink = () => API + DATA.support.whatsapp;
const minutesLabel = (m) => (m >= 60 ? `${Math.floor(m / 60)} ч ${m % 60 ? (m % 60) + " мин" : ""}` : `${m} мин`).trim();

function setNav(p, active) {
  topnav.innerHTML = p
    ? [["", "Обзор"], ["att", "Насадки"], ["rec", "Рецепты"], ["care", "Уход"], ["help", "Помощь"]]
        .map(([k, l]) => `<a href="#/${p.id}${k ? "/" + k : ""}" class="${active === k ? "on" : ""}">${l}</a>`).join("")
    : "";
}

function home() {
  setNav(null);
  app.innerHTML = `
    <section class="home-hero">
      <p class="eyebrow">ATARIA</p>
      <h1 style="margin-top:14px">Готовим вместе</h1>
      <p class="lead">Рецепты, насадки и простые советы для вашей техники ATARIA. Выберите, что у вас дома.</p>
      <div class="pick">
        ${DATA.products.map((p) => p.status === "soon" ? `
          <div class="pick-card soon"><span class="badge">Скоро</span>
            <div class="ph">${ICONS.airfryer}</div>
            <div class="body"><p class="eyebrow">${esc(p.kind)}</p><h3>${esc(p.name)}</h3><p class="lead" style="font-size:15px">${esc(p.tagline)}</p></div>
          </div>` : `
          <a class="pick-card" href="#/${p.id}">
            <div class="ph"><img src="${esc(p.hero)}" alt="${esc(p.name)}"></div>
            <div class="body"><p class="eyebrow">${esc(p.kind)}</p><h3>${esc(p.name)}</h3><p class="lead" style="font-size:15px">${esc(p.tagline)}</p></div>
          </a>`).join("")}
      </div>
    </section>`;
}

function overview(p) {
  setNav(p, "");
  app.innerHTML = `
    <div class="p-hero">
      <div class="txt">
        <p class="eyebrow">${esc(p.kind)}</p>
        <h1>${esc(p.name)}</h1>
        <div class="rule"></div>
        <p class="lead">${esc(p.intro)}</p>
        <div class="actions">
          <a class="btn" href="#/${p.id}/start">С чего начать</a>
          <a class="btn ghost" href="#/${p.id}/rec">Рецепты</a>
        </div>
      </div>
      <div class="ph"><img src="${esc(p.hero)}" alt="${esc(p.name)}"></div>
    </div>
    <div class="specs">${p.specs.map((s) => `<div class="spec"><div class="k">${esc(s.label)}</div><div class="v">${esc(s.value)}</div></div>`).join("")}</div>

    <div class="story">
      <div class="ph"><img src="img/sm23-host.jpg" alt="Хозяйка засыпает муку в чашу ATARIA" loading="lazy"></div>
      <div class="txt">
        <p class="eyebrow">Как это бывает дома</p>
        <blockquote>«Засыпала муку, нажала кнопку и пошла резать лук. Через три минуты тесто для беша готово, руки чистые»</blockquote>
        <p class="lead" style="font-size:15px">Машина берёт на себя самое тяжёлое: замес, фарш, раскатку. Вам остаётся самое приятное.</p>
        <div class="actions" style="margin-top:4px"><a class="btn ghost" href="#/${p.id}/r/besh">Рецепт теста для беша</a></div>
      </div>
    </div>

    <section>
      <div class="sec-head"><h2>Какая скорость для какой насадки</h2></div>
      <div class="speeds">${p.speeds.map((s) => `
        <a href="#/${p.id}/a/${s.attachment}"><span class="nm">${esc(s.name)}</span><span class="rg">${esc(s.range)}</span><span class="fo">${esc(s.for)}</span></a>`).join("")}
      </div>
      <p class="lead" style="font-size:14px;margin-top:12px">Всегда начинайте со скорости 1 и прибавляйте постепенно.</p>
    </section>

    <section>
      <div class="sec-head"><h2>Насадки</h2><a href="#/${p.id}/att">Все насадки →</a></div>
      ${attGrid(p, p.attachments.slice(0, 4))}
    </section>

    <section>
      <div class="sec-head"><h2>Что приготовить</h2><a href="#/${p.id}/rec">Все рецепты →</a></div>
      ${recGrid(p, p.recipes.slice(0, 4))}
    </section>

    ${supportBlock(p)}`;
}

function start(p) {
  setNav(p, "");
  app.innerHTML = `
    <a class="back" href="#/${p.id}">← ${esc(p.name)}</a>
    <section style="padding-top:20px">
      <p class="eyebrow">Первый запуск</p>
      <h1 style="margin-top:12px">С чего начать</h1>
      <div class="rule"></div>
      <div class="steps">${p.quickstart.map((s, i) => `
        <div class="step"><div class="n">${i + 1}</div><div><h3>${esc(s.title)}</h3><p>${esc(s.text)}</p></div></div>`).join("")}
      </div>
    </section>
    <section>
      <div class="sec-head"><h2>Что где на машине</h2></div>
      <div class="detail" style="padding-top:0">
        <div class="ph"><img src="img/dial.jpg" alt="Регулятор скорости"></div>
        <div class="parts">${p.parts.map((x) => `<div class="part"><h3>${esc(x.name)}</h3><p>${esc(x.text)}</p></div>`).join("")}</div>
      </div>
    </section>`;
}

function attGrid(p, list) {
  return `<div class="grid">${list.map((a) => `
    <a class="card" href="#/${p.id}/a/${a.id}">
      <div class="ph">${media(a)}</div>
      <div class="body"><span class="meta">${esc(a.group)}${a.speed ? " · скорость " + esc(a.speed) : ""}</span><h3>${esc(a.name)}</h3><span class="meta">${esc(a.short)}</span></div>
    </a>`).join("")}</div>`;
}

function recGrid(p, list) {
  return `<div class="grid">${list.map((r) => `
    <a class="card" href="#/${p.id}/r/${r.id}">
      <div class="ph">${r.image ? `<img src="${esc(r.image)}" alt="${esc(r.title)}" loading="lazy">` : ""}</div>
      <div class="body"><span class="meta">${esc(r.tag)} · ${esc(r.time)}</span><h3>${esc(r.title)}</h3>
        <div class="chips">${r.attachments.map((id) => `<span class="chip">${esc(att(p, id)?.name || id)}</span>`).join("")}</div></div>
    </a>`).join("")}</div>`;
}

function attachments(p) {
  setNav(p, "att");
  const groups = [...new Set(p.attachments.map((a) => a.group))];
  app.innerHTML = `
    <section style="padding-top:40px">
      <p class="eyebrow">${esc(p.name)}</p>
      <h1 style="margin-top:12px">Насадки</h1>
      <div class="rule"></div>
      <p class="lead">В чаше месим и взбиваем. Спереди крутим, трём, раскатываем и режем. Сверху блендер.</p>
    </section>
    ${groups.map((g) => `<section style="padding-top:28px"><p class="eyebrow" style="margin-bottom:14px">${esc(g)}</p>${attGrid(p, p.attachments.filter((a) => a.group === g))}</section>`).join("")}`;
}

function attachment(p, a) {
  setNav(p, "att");
  const recs = p.recipes.filter((r) => r.attachments.includes(a.id));
  app.innerHTML = `
    <a class="back" href="#/${p.id}/att">← Все насадки</a>
    <div class="detail">
      <div class="ph">${media(a)}</div>
      <div>
        <p class="eyebrow">${esc(a.group)}</p>
        <h1 style="margin-top:10px">${esc(a.name)}</h1>
        <div class="rule"></div>
        <p class="lead">${esc(a.what)}</p>
        ${a.speed ? `<div class="speedbig"><span class="eyebrow">Скорость</span><b>${esc(a.speed)}</b></div>` : ""}
        <div class="block"><h3>Подходит для</h3><div class="chips">${a.use_for.map((u) => `<span class="chip">${esc(u)}</span>`).join("")}</div></div>
        ${a.kit ? `<div class="block"><h3>В комплекте</h3><ul class="clean">${a.kit.map((k) => `<li>${esc(k)}</li>`).join("")}</ul></div>` : ""}
        <div class="block"><h3>Как пользоваться</h3><ul class="clean">${a.how.map((k) => `<li>${esc(k)}</li>`).join("")}</ul></div>
        <div class="block"><h3>Совет</h3><ul class="clean">${a.tips.map((k) => `<li>${esc(k)}</li>`).join("")}</ul></div>
        <div class="block"><h3>Чего не делать</h3><ul class="clean warn">${a.dont.map((k) => `<li>${esc(k)}</li>`).join("")}</ul></div>
      </div>
    </div>
    ${recs.length ? `<section><div class="sec-head"><h2>Рецепты с этой насадкой</h2></div>${recGrid(p, recs)}</section>` : ""}`;
}

function recipes(p, filter = "Все") {
  setNav(p, "rec");
  const tags = ["Все", ...new Set(p.recipes.map((r) => r.tag))];
  const list = filter === "Все" ? p.recipes : p.recipes.filter((r) => r.tag === filter);
  app.innerHTML = `
    <section style="padding-top:40px">
      <p class="eyebrow">${esc(p.name)}</p>
      <h1 style="margin-top:12px">Рецепты</h1>
      <div class="rule"></div>
      <p class="lead">Проверенные рецепты с точными скоростями. Откройте рецепт и нажмите «Готовить по шагам»: крупный текст и таймер прямо в телефоне.</p>
    </section>
    <div class="filters">${tags.map((t) => `<button data-tag="${esc(t)}" class="${t === filter ? "on" : ""}">${esc(t)}</button>`).join("")}</div>
    ${recGrid(p, list)}`;
  app.querySelectorAll(".filters button").forEach((b) => b.addEventListener("click", () => recipes(p, b.dataset.tag)));
}

function recipe(p, r) {
  setNav(p, "rec");
  app.innerHTML = `
    <a class="back" href="#/${p.id}/rec">← Все рецепты</a>
    <div class="detail">
      <div class="ph">${r.image ? `<img src="${esc(r.image)}" alt="${esc(r.title)}">` : ""}</div>
      <div>
        <p class="eyebrow">${esc(r.tag)} · ${esc(r.time)} · ${esc(r.servings)}</p>
        <h1 style="margin-top:10px">${esc(r.title)}</h1>
        <div class="rule"></div>
        <p class="lead">${esc(r.intro)}</p>
        <div class="chips" style="margin-top:16px">${r.attachments.map((id) => `<a class="chip" href="#/${p.id}/a/${id}" style="text-decoration:none">${esc(att(p, id)?.name || id)}</a>`).join("")}</div>
        <div class="actions"><button class="btn" id="cook">Готовить по шагам</button></div>
        <div class="block"><h3>Продукты</h3><ul class="clean ings">${r.ingredients.map((i) => `<li>${esc(i)}</li>`).join("")}</ul></div>
        <div class="block"><h3>Как готовить</h3><div class="rsteps">${r.steps.map((s, i) => `
          <div class="rstep"><div class="n">${i + 1}</div><div><p>${esc(s.text)}</p><div class="tags">
            ${s.attachment ? `<span class="chip">${esc(att(p, s.attachment)?.name || "")}</span>` : ""}
            ${s.speed ? `<span class="chip">скорость ${esc(s.speed)}</span>` : ""}
            ${s.minutes ? `<span class="chip">${esc(minutesLabel(s.minutes))}</span>` : ""}</div></div></div>`).join("")}
        </div></div>
      </div>
    </div>
    ${reviewBlock(p)}`;
  document.getElementById("cook").addEventListener("click", () => cook(p, r));
}

function cook(p, r) {
  let i = 0, left = 0, timer = null;
  const el = document.createElement("div");
  el.className = "cook";
  document.body.appendChild(el);
  document.body.style.overflow = "hidden";
  let wake = null;
  if (navigator.wakeLock) navigator.wakeLock.request("screen").then((w) => (wake = w)).catch(() => {});
  const stop = () => { clearInterval(timer); timer = null; };
  const close = () => { stop(); wake?.release?.(); el.remove(); document.body.style.overflow = ""; };
  const fmt = (s) => `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
  const draw = () => {
    const s = r.steps[i];
    el.innerHTML = `
      <div class="bar"><span class="eyebrow">${esc(r.title)} · шаг ${i + 1} из ${r.steps.length}</span><button class="x" id="cx">Закрыть</button></div>
      <div class="prog"><i style="width:${((i + 1) / r.steps.length) * 100}%"></i></div>
      <div class="main">
        <p class="txt">${esc(s.text)}</p>
        <div class="chips">${s.attachment ? `<span class="chip">${esc(att(p, s.attachment)?.name || "")}</span>` : ""}${s.speed ? `<span class="chip">скорость ${esc(s.speed)}</span>` : ""}</div>
        ${s.minutes ? `<div class="timer"><span class="t" id="tt">${fmt(left || s.minutes * 60)}</span><button class="btn ghost" id="tgo">${timer ? "Пауза" : "Запустить таймер"}</button></div>` : ""}
      </div>
      <div class="nav"><button class="btn ghost" id="prev" ${i === 0 ? "disabled" : ""}>Назад</button>
        <button class="btn" id="next">${i === r.steps.length - 1 ? "Готово" : "Дальше"}</button></div>`;
    el.querySelector("#cx").onclick = close;
    el.querySelector("#prev").onclick = () => { if (i > 0) { stop(); left = 0; i--; draw(); } };
    el.querySelector("#next").onclick = () => { stop(); left = 0; if (i < r.steps.length - 1) { i++; draw(); } else { close(); location.hash = `#/${p.id}/done/${r.id}`; } };
    const go = el.querySelector("#tgo");
    if (go) go.onclick = () => {
      if (timer) { stop(); draw(); return; }
      if (!left) left = s.minutes * 60;
      timer = setInterval(() => {
        left--;
        const t = el.querySelector("#tt"); if (t) t.textContent = fmt(Math.max(0, left));
        if (left <= 0) { stop(); left = 0; navigator.vibrate?.([300, 150, 300]); const t2 = el.querySelector("#tt"); if (t2) t2.textContent = "Готово"; }
      }, 1000);
      draw();
    };
  };
  draw();
}

function done(p, r) {
  setNav(p, "rec");
  app.innerHTML = `
    <section class="home-hero">
      <p class="eyebrow">${esc(r.title)}</p>
      <h1 style="margin-top:14px">Приятного аппетита!</h1>
      <p class="lead">Надеемся, получилось вкусно.</p>
    </section>
    ${reviewBlock(p, true)}
    <section><div class="sec-head"><h2>Что приготовить ещё</h2></div>${recGrid(p, p.recipes.filter((x) => x.id !== r.id).slice(0, 4))}</section>`;
}

function reviewBlock(p, big = false) {
  const k = DATA.support.kaspi_review;
  if (!k) return "";
  return `<section><div class="support"><div class="box">
    <p class="eyebrow">Вам нравится ${esc(p.name)}?</p>
    <h3>${big ? "Оставьте отзыв на Kaspi, это займёт минуту" : "Будем рады вашему отзыву на Kaspi"}</h3>
    <p class="lead" style="font-size:15px">Отзыв помогает другим выбрать и нам становиться лучше.</p>
    <div class="actions" style="margin-top:6px"><a class="btn" href="${esc(k)}" target="_blank" rel="noopener">Оставить отзыв на Kaspi</a></div>
  </div></div></section>`;
}

function supportBlock(p) {
  return `<section><div class="support">
    <div class="box"><p class="eyebrow">Помощь</p><h3>Что-то не получается?</h3><p class="lead" style="font-size:15px">Напишите нам в WhatsApp, подскажем по насадкам, скоростям и рецептам.</p>
      <div class="actions" style="margin-top:6px"><a class="btn" href="${esc(waLink())}" target="_blank" rel="noopener">Написать в WhatsApp</a></div></div>
    ${DATA.support.kaspi_review ? `<div class="box"><p class="eyebrow">Отзыв</p><h3>Понравилась машина?</h3><p class="lead" style="font-size:15px">Пара слов на Kaspi очень помогает.</p>
      <div class="actions" style="margin-top:6px"><a class="btn ghost" href="${esc(DATA.support.kaspi_review)}" target="_blank" rel="noopener">Оставить отзыв</a></div></div>` : ""}
  </div></section>`;
}

function care(p) {
  setNav(p, "care");
  app.innerHTML = `
    <section style="padding-top:40px">
      <p class="eyebrow">${esc(p.name)}</p>
      <h1 style="margin-top:12px">Уход и безопасность</h1>
      <div class="rule"></div>
      <p class="lead">Несколько простых привычек, и машина прослужит долгие годы.</p>
    </section>
    <div class="parts">${p.care.map((c) => `<div class="part"><h3>${esc(c.title)}</h3><p>${esc(c.text)}</p></div>`).join("")}</div>
    <section><div class="sec-head"><h2>Важно</h2></div><ul class="clean warn">${p.safety.map((s) => `<li>${esc(s)}</li>`).join("")}</ul></section>`;
}

function help(p) {
  setNav(p, "help");
  app.innerHTML = `
    <section style="padding-top:40px">
      <p class="eyebrow">${esc(p.name)}</p>
      <h1 style="margin-top:12px">Вопросы и помощь</h1>
      <div class="rule"></div>
    </section>
    <div>${p.faq.map((f) => `<details class="faq"><summary>${esc(f.q)}</summary><p>${esc(f.a)}</p></details>`).join("")}</div>
    ${supportBlock(p)}`;
}

function route() {
  const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  const p = parts[0] && product(parts[0]);
  window.scrollTo(0, 0);
  if (!p || p.status !== "active") return home();
  const [, kind, id] = parts;
  if (!kind) return overview(p);
  if (kind === "start") return start(p);
  if (kind === "att") return attachments(p);
  if (kind === "a" && att(p, id)) return attachment(p, att(p, id));
  if (kind === "rec") return recipes(p);
  if (kind === "r" && p.recipes.find((r) => r.id === id)) return recipe(p, p.recipes.find((r) => r.id === id));
  if (kind === "done" && p.recipes.find((r) => r.id === id)) return done(p, p.recipes.find((r) => r.id === id));
  if (kind === "care") return care(p);
  if (kind === "help") return help(p);
  overview(p);
}

fetch("content.json").then((r) => r.json()).then((d) => {
  DATA = d;
  document.getElementById("foot-wa").href = waLink();
  addEventListener("hashchange", route);
  route();
}).catch(() => { app.innerHTML = '<section><p class="lead">Не удалось загрузить данные. Обновите страницу.</p></section>'; });
