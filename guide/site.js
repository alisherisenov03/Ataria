// Menu, language, search, recipe filter and step-by-step cook mode. All page content is pre-rendered HTML.
const $ = (s, r = document) => r.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const LANG = document.documentElement.lang === "kk" ? "kk" : "ru";
const PREFIX = LANG === "kk" ? "/kk" : "";

// ---- old #/ links (from the first version) -> real pages ----
if (location.hash.startsWith("#/")) {
  const [pid, kind, id] = location.hash.slice(2).split("/");
  const map = { att: "attachments", rec: "recipes", a: "attachments", r: "recipes" };
  if (pid) location.replace("/" + [pid, map[kind] || kind, id].filter(Boolean).join("/") + "/");
}

// ---- language: remember the choice, open the home page in the saved language ----
try {
  document.querySelectorAll(".lang a").forEach((a) => a.addEventListener("click", () => localStorage.setItem("lang", a.dataset.lang)));
  const saved = localStorage.getItem("lang");
  if (location.pathname === "/" && saved === "kk" && !document.referrer.includes(location.host)) location.replace("/kk/");
} catch (e) { /* storage may be blocked */ }

// ---- drawer ----
const drawer = $("#drawer");
$("#open-menu")?.addEventListener("click", () => { drawer.hidden = false; });
$("#close-menu")?.addEventListener("click", () => { drawer.hidden = true; });
drawer?.addEventListener("click", (e) => { if (e.target === drawer) drawer.hidden = true; });

// ---- search ----
let INDEX = null;
const indexUrl = LANG === "kk" ? "/search-index-kk.json" : "/search-index.json";
const load = () => INDEX ? Promise.resolve(INDEX) : fetch(indexUrl).then((r) => r.json()).then((d) => (INDEX = d)).catch(() => (INDEX = []));
const norm = (s) => s.toLowerCase().replace(/ё/g, "е").replace(/ү/g, "у").replace(/ұ/g, "у").replace(/қ/g, "к").replace(/ғ/g, "г").replace(/ң/g, "н").replace(/ө/g, "о").replace(/і/g, "и").replace(/ә/g, "а").replace(/һ/g, "х");
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
function bind(input, box, emptyText) {
  input.addEventListener("input", async () => {
    await load();
    const q = input.value.trim();
    if (!q) { box.innerHTML = ""; return; }
    const res = find(q);
    box.innerHTML = res.length
      ? res.map((e) => `<a href="${esc(e.u)}"><span class="k">${esc(e.k)}</span><span class="t">${esc(e.t)}</span></a>`).join("")
      : `<p class="empty">${esc(emptyText)}</p>`;
  });
}
const search = $("#search");
if (search) {
  bind($("#q"), $("#results"), search.dataset.empty);
  $("#open-search").addEventListener("click", () => { search.hidden = false; $("#q").focus(); });
  $("#hero-search")?.addEventListener("click", () => { search.hidden = false; $("#q").focus(); });
  $("#close-search").addEventListener("click", () => { search.hidden = true; });
  addEventListener("keydown", (e) => { if (e.key === "Escape") { search.hidden = true; drawer.hidden = true; } });
}
if ($("#q2")) { bind($("#q2"), $("#results2"), $("#search2").dataset.empty); const q = new URLSearchParams(location.search).get("q"); if (q) { $("#q2").value = q; $("#q2").dispatchEvent(new Event("input")); } }

// ---- recipe filter ----
const filters = $("#filters");
if (filters) filters.addEventListener("click", (e) => {
  const b = e.target.closest("button"); if (!b) return;
  filters.querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
  document.querySelectorAll("#rgrid .card").forEach((c) => { c.hidden = b.dataset.all !== "1" && c.dataset.tag !== b.dataset.tag; });
});

// ---- cook mode ----
const cookBtn = $("#cook");
if (cookBtn) cookBtn.addEventListener("click", () => {
  const r = JSON.parse($("#recipe-data").textContent);
  const t = r.labels;
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
      <div class="bar"><span class="eyebrow">${esc(r.title)} · ${esc(t.step)} ${i + 1} ${esc(t.of)} ${r.steps.length}</span><button class="x" id="cx">${esc(t.close)}</button></div>
      <div class="prog"><i style="width:${((i + 1) / r.steps.length) * 100}%"></i></div>
      <div class="main">
        <p class="txt">${esc(s.text)}</p>
        <div class="chips">${s.attachmentName ? `<span class="chip">${esc(s.attachmentName)}</span>` : ""}${s.speed ? `<span class="chip">${esc(t.speed)} ${esc(s.speed)}</span>` : ""}</div>
        ${s.minutes ? `<div class="timer"><span class="t" id="tt">${fmt(left || s.minutes * 60)}</span><button class="btn ghost" id="tgo">${esc(timer ? t.pause : t.start)}</button></div>` : ""}
      </div>
      <div class="nav"><button class="btn ghost" id="prev" ${i === 0 ? "disabled" : ""}>${esc(t.back)}</button>
        <button class="btn" id="next">${esc(i === r.steps.length - 1 ? t.done : t.next)}</button></div>`;
    $("#cx", el).onclick = close;
    $("#prev", el).onclick = () => { if (i > 0) { stop(); left = 0; i--; draw(); } };
    $("#next", el).onclick = () => { stop(); left = 0; if (i < r.steps.length - 1) { i++; draw(); } else { close(); location.href = r.doneUrl; } };
    const go = $("#tgo", el);
    if (go) go.onclick = () => {
      if (timer) { stop(); draw(); return; }
      if (!left) left = s.minutes * 60;
      timer = setInterval(() => {
        left--;
        const tt = $("#tt", el); if (tt) tt.textContent = fmt(Math.max(0, left));
        if (left <= 0) { stop(); left = 0; navigator.vibrate?.([300, 150, 300]); const t2 = $("#tt", el); if (t2) t2.textContent = t.done; }
      }, 1000);
      draw();
    };
  };
  draw();
});

// ---- multi-angle viewer: tabs + drag/swipe through real photos of the machine ----
const vstage = $("#vstage");
if (vstage) {
  const imgs = [...vstage.querySelectorAll("img")], tabs = [...document.querySelectorAll("#vtabs button")];
  let cur = 0, sx = null, acc = 0;
  const show = (i) => { cur = (i + imgs.length) % imgs.length; imgs.forEach((im, k) => im.classList.toggle("on", k === cur)); tabs.forEach((t, k) => t.classList.toggle("on", k === cur)); };
  show(0);
  tabs.forEach((t, k) => t.addEventListener("click", () => show(k)));
  vstage.addEventListener("pointerdown", (e) => { sx = e.clientX; acc = 0; vstage.setPointerCapture(e.pointerId); });
  vstage.addEventListener("pointermove", (e) => {
    if (sx === null) return;
    acc += e.clientX - sx; sx = e.clientX;
    if (Math.abs(acc) > 70) { show(cur + (acc < 0 ? 1 : -1)); acc = 0; }
  });
  ["pointerup", "pointercancel"].forEach((ev) => vstage.addEventListener(ev, () => { sx = null; }));
  vstage.tabIndex = 0;
  vstage.addEventListener("keydown", (e) => { if (e.key === "ArrowRight") show(cur + 1); if (e.key === "ArrowLeft") show(cur - 1); });
}
