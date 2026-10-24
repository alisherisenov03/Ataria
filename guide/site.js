// Menu, search, recipe filter and step-by-step cook mode. All page content is pre-rendered HTML.
const $ = (s, r = document) => r.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// ---- old #/ links (from the first version) -> real pages ----
if (location.hash.startsWith("#/")) {
  const [pid, kind, id] = location.hash.slice(2).split("/");
  const map = { att: "attachments", rec: "recipes", a: "attachments", r: "recipes" };
  if (pid) location.replace("/" + [pid, map[kind] || kind, id].filter(Boolean).join("/") + "/");
}

// ---- drawer ----
const drawer = $("#drawer");
$("#open-menu")?.addEventListener("click", () => { drawer.hidden = false; });
$("#close-menu")?.addEventListener("click", () => { drawer.hidden = true; });
drawer?.addEventListener("click", (e) => { if (e.target === drawer) drawer.hidden = true; });

// ---- search ----
let INDEX = null;
const load = () => INDEX ? Promise.resolve(INDEX) : fetch("/search-index.json").then((r) => r.json()).then((d) => (INDEX = d)).catch(() => (INDEX = []));
const norm = (s) => s.toLowerCase().replace(/ё/g, "е");
function find(q) {
  const words = norm(q).split(/\s+/).filter((w) => w.length > 1);
  if (!words.length) return [];
  return INDEX.map((e) => {
    const title = norm(e.t), text = norm(e.x);
    let score = 0;
    for (const w of words) {
      const stem = w.length > 5 ? w.slice(0, -1) : w;
      if (title.includes(stem)) score += 3; else if (text.includes(stem)) score += 1; else return null;
    }
    return { e, score };
  }).filter(Boolean).sort((a, b) => b.score - a.score).slice(0, 12).map((x) => x.e);
}
function bind(input, box) {
  input.addEventListener("input", async () => {
    await load();
    const q = input.value.trim();
    if (!q) { box.innerHTML = ""; return; }
    const res = find(q);
    box.innerHTML = res.length
      ? res.map((e) => `<a href="${esc(e.u)}"><span class="k">${esc(e.k)}</span><span class="t">${esc(e.t)}</span></a>`).join("")
      : `<p class="empty">Ничего не нашли. Напишите нам в WhatsApp, подскажем.</p>`;
  });
}
const search = $("#search");
if (search) {
  bind($("#q"), $("#results"));
  $("#open-search").addEventListener("click", () => { search.hidden = false; $("#q").focus(); });
  $("#close-search").addEventListener("click", () => { search.hidden = true; });
  addEventListener("keydown", (e) => { if (e.key === "Escape") { search.hidden = true; drawer.hidden = true; } });
}
if ($("#q2")) { bind($("#q2"), $("#results2")); const q = new URLSearchParams(location.search).get("q"); if (q) { $("#q2").value = q; $("#q2").dispatchEvent(new Event("input")); } }

// ---- recipe filter ----
const filters = $("#filters");
if (filters) filters.addEventListener("click", (e) => {
  const b = e.target.closest("button"); if (!b) return;
  filters.querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
  document.querySelectorAll("#rgrid .card").forEach((c) => { c.hidden = b.dataset.tag !== "Все" && c.dataset.tag !== b.dataset.tag; });
});

// ---- cook mode ----
const cookBtn = $("#cook");
if (cookBtn) cookBtn.addEventListener("click", () => {
  const r = JSON.parse($("#recipe-data").textContent);
  let i = 0, left = 0, timer = null, wake = null;
  const el = document.createElement("div");
  el.className = "cook";
  document.body.append(el);
  document.body.style.overflow = "hidden";
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
        <div class="chips">${s.attachmentName ? `<span class="chip">${esc(s.attachmentName)}</span>` : ""}${s.speed ? `<span class="chip">скорость ${esc(s.speed)}</span>` : ""}</div>
        ${s.minutes ? `<div class="timer"><span class="t" id="tt">${fmt(left || s.minutes * 60)}</span><button class="btn ghost" id="tgo">${timer ? "Пауза" : "Запустить таймер"}</button></div>` : ""}
      </div>
      <div class="nav"><button class="btn ghost" id="prev" ${i === 0 ? "disabled" : ""}>Назад</button>
        <button class="btn" id="next">${i === r.steps.length - 1 ? "Готово" : "Дальше"}</button></div>`;
    $("#cx", el).onclick = close;
    $("#prev", el).onclick = () => { if (i > 0) { stop(); left = 0; i--; draw(); } };
    $("#next", el).onclick = () => { stop(); left = 0; if (i < r.steps.length - 1) { i++; draw(); } else { close(); location.href = `/sm23/recipes/${r.id}/done/`; } };
    const go = $("#tgo", el);
    if (go) go.onclick = () => {
      if (timer) { stop(); draw(); return; }
      if (!left) left = s.minutes * 60;
      timer = setInterval(() => {
        left--;
        const t = $("#tt", el); if (t) t.textContent = fmt(Math.max(0, left));
        if (left <= 0) { stop(); left = 0; navigator.vibrate?.([300, 150, 300]); const t2 = $("#tt", el); if (t2) t2.textContent = "Готово"; }
      }, 1000);
      draw();
    };
  };
  draw();
});
