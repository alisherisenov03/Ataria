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

// ---- servings: scale ingredients to the number of people ----
const ingBox = $("#ingbox");
if (ingBox) {
  const base = +ingBox.dataset.base || 4;
  const btns = [...ingBox.querySelectorAll("#people button")];
  const cells = [...ingBox.querySelectorAll("td[data-q]")];
  const yieldEl = $("#yield");
  const FR = ["", "¼", "½", "¾"];
  const frac = (v) => { const q = Math.round(v * 4) / 4, w = Math.floor(q), f = Math.round((q - w) * 4); return (w ? String(w) : "") + FR[f] || "¼"; };
  const dec = (v) => String(Math.round(v * 10) / 10).replace(".", ",");
  function scaleQty(q, f) {
    const m = q.match(/^(\d+(?:[.,]\d+)?)(?:(\s*[–-]\s*)(\d+(?:[.,]\d+)?))?([\s\S]*)$/);
    if (!m) return q;
    const lat = (x) => parseFloat(x.replace(",", "."));
    let tail = m[4], unit = tail.trim().toLowerCase();
    const conv = (n) => {
      let v = n * f, u = tail;
      if (/^кг/.test(unit)) { v *= 1000; u = u.replace("кг", "г"); }
      if (/^(г|мл)(\s|$|\.|,)/.test(u.trim().toLowerCase() + " ")) {
        v = v < 50 ? Math.round(v / 5) * 5 : v < 1000 ? Math.round(v / 10) * 10 : Math.round(v / 50) * 50;
        if (v >= 1000) { u = u.replace(/г/, "кг").replace(/мл/, "л"); return [dec(v / 1000), u]; }
        return [String(Math.max(v, 5)), u];
      }
      if (/^(шт|дана|ломтик|зубчик|зуб|тіс|бөлік)/.test(unit)) { v = v < 3 ? Math.round(v * 2) / 2 : Math.round(v); return [v < 1 ? "½" : /\./.test(String(v)) ? frac(v) : String(v), u]; }
      return [v >= 10 ? String(Math.round(v)) : frac(Math.max(v, .25)), u];
    };
    const [a, u] = conv(lat(m[1]));
    if (m[3]) { const [b] = conv(lat(m[3])); return a + m[2] + b + u; }
    return a + u;
  }
  const scaleYield = (str, f) => str.replace(/\d+/g, (n) => String(Math.max(1, Math.round(n * f))));
  function apply(n, btn) {
    const f = n / base;
    btns.forEach((b) => b.classList.toggle("on", b === btn));
    cells.forEach((c) => { c.textContent = scaleQty(c.dataset.q, f); });
    if (yieldEl) yieldEl.textContent = ingBox.dataset.scaleYield === "1" ? scaleYield(ingBox.dataset.yield, f) : ingBox.dataset.people.replace("{n}", btn.querySelector("b").textContent);
    const note = $("#scale-note");
    if (note) { note.hidden = f < 1.5 || !ingBox.dataset.note; note.textContent = ingBox.dataset.note; }
    try { localStorage.setItem("people", String(n)); } catch (e) { /* ignore */ }
  }
  btns.forEach((b) => b.addEventListener("click", () => apply(+b.dataset.n, b)));
  let want = base;
  try { const sv = +localStorage.getItem("people"); if (sv) want = sv; } catch (e) { /* ignore */ }
  const start = btns.reduce((best, b) => (Math.abs(+b.dataset.n - want) < Math.abs(+best.dataset.n - want) ? b : best), btns[0]);
  apply(+start.dataset.n, start);
}

// ---- timer service worker (needed for the "time is up" notification) ----
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});

// ---- cook mode ----
const TKEY = "ataria_timer";
const readT = () => { try { return JSON.parse(localStorage.getItem(TKEY)); } catch (e) { return null; } };
const saveT = (v) => { try { v ? localStorage.setItem(TKEY, JSON.stringify(v)) : localStorage.removeItem(TKEY); } catch (e) { /* ignore */ } };
// 1 second of silence: playing it keeps the page (and its timer) alive while the screen is locked
const silentWav = (() => {
  const n = 8000, b = new Uint8Array(44 + n), dv = new DataView(b.buffer);
  const w = (o, s) => [...s].forEach((c, k) => b.set([c.charCodeAt(0)], o + k));
  w(0, "RIFF"); dv.setUint32(4, 36 + n, true); w(8, "WAVEfmt "); dv.setUint32(16, 16, true); dv.setUint16(20, 1, true); dv.setUint16(22, 1, true);
  dv.setUint32(24, 8000, true); dv.setUint32(28, 8000, true); dv.setUint16(32, 1, true); dv.setUint16(34, 8, true); w(36, "data"); dv.setUint32(40, n, true); b.fill(128, 44);
  let s = ""; b.forEach((x) => (s += String.fromCharCode(x))); return "data:audio/wav;base64," + btoa(s);
})();

const cookBtn = $("#cook");
if (cookBtn) {
  const r = JSON.parse($("#recipe-data").textContent);
  const t = r.labels;
  const open = (startI = 0, resumeEnd = 0) => {
    let i = startI, left = 0, endAt = resumeEnd, timer = null, beepTimer = null, ringing = false, wake = null, ctx = null, keep = null;
    const el = document.createElement("div");
    el.className = "cook";
    document.body.append(el);
    document.body.style.overflow = "hidden";
    const lock = () => { if (navigator.wakeLock) navigator.wakeLock.request("screen").then((w) => (wake = w)).catch(() => {}); };
    lock();
    const remaining = () => (endAt ? Math.max(0, Math.ceil((endAt - Date.now()) / 1000)) : left);
    const fmt = (s) => `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
    const unlock = () => {
      try { ctx = ctx || new (window.AudioContext || window.webkitAudioContext)(); ctx.resume(); } catch (e) { /* ignore */ }
      try { if (!keep) { keep = new Audio(silentWav); keep.loop = true; keep.volume = .01; } keep.play().catch(() => {}); } catch (e) { /* ignore */ }
      if ("Notification" in window && Notification.permission === "default") Notification.requestPermission().catch(() => {});
    };
    const stopKeep = () => { try { keep?.pause(); } catch (e) { /* ignore */ } };
    const clearTimer = () => { clearInterval(timer); timer = null; };
    const stopAlarm = () => { clearInterval(beepTimer); beepTimer = null; ringing = false; stopKeep(); };
    const hardStop = () => { clearTimer(); endAt = 0; left = 0; saveT(null); stopAlarm(); };
    const close = () => { hardStop(); wake?.release?.(); document.removeEventListener("visibilitychange", onVis); el.remove(); document.body.style.overflow = ""; };
    const beep = () => {
      if (!ctx) return;
      [0, .32].forEach((d) => {
        const o = ctx.createOscillator(), g = ctx.createGain(), at = ctx.currentTime + d;
        o.frequency.value = 880; o.connect(g); g.connect(ctx.destination);
        g.gain.setValueAtTime(.0001, at); g.gain.exponentialRampToValueAtTime(.4, at + .02); g.gain.exponentialRampToValueAtTime(.0001, at + .25);
        o.start(at); o.stop(at + .28);
      });
    };
    const notify = () => {
      if (!("Notification" in window) || Notification.permission !== "granted") return;
      navigator.serviceWorker?.getRegistration().then((reg) => {
        const opts = { body: t.notifyBody, tag: "ataria-timer", requireInteraction: true, vibrate: [300, 150, 300], icon: "/img/icon-192.png", data: { url: location.href } };
        if (reg) reg.showNotification(t.notifyTitle, opts); else new Notification(t.notifyTitle, opts);
      }).catch(() => {});
    };
    const ring = () => {
      clearTimer(); endAt = 0; left = 0; saveT(null); ringing = true;
      navigator.vibrate?.([300, 150, 300, 150, 300]);
      beep(); beepTimer = setInterval(() => { beep(); navigator.vibrate?.([300, 150, 300]); }, 1500);
      notify(); draw();
    };
    const tick = () => {
      if (!el.isConnected) return;
      const rem = remaining(), tt = $("#tt", el);
      if (tt && !ringing) tt.textContent = fmt(rem);
      if (endAt && rem <= 0) ring();
    };
    const loop = () => { clearTimer(); timer = setInterval(tick, 500); };
    function onVis() { if (document.visibilityState === "visible") { lock(); tick(); } }
    document.addEventListener("visibilitychange", onVis);
    const draw = () => {
      const s = r.steps[i];
      const shown = ringing ? t.alarm : fmt(remaining() || s.minutes * 60);
      el.innerHTML = `
        <div class="bar"><span class="eyebrow">${esc(r.title)} · ${esc(t.step)} ${i + 1} ${esc(t.of)} ${r.steps.length}</span><button class="x" id="cx">${esc(t.close)}</button></div>
        <div class="prog"><i style="width:${((i + 1) / r.steps.length) * 100}%"></i></div>
        <div class="main">
          <p class="txt">${esc(s.text)}</p>
          <div class="chips">${s.attachmentName ? `<span class="chip">${esc(s.attachmentName)}</span>` : ""}${s.speed ? `<span class="chip">${esc(t.speed)} ${esc(s.speed)}</span>` : ""}</div>
          ${s.minutes ? `<div class="timer${ringing ? " ring" : ""}"><span class="t" id="tt">${esc(shown)}</span><button class="btn ghost" id="tgo">${esc(ringing ? t.stopSound : endAt ? t.pause : t.start)}</button></div>` : ""}
        </div>
        <div class="nav"><button class="btn ghost" id="prev" ${i === 0 ? "disabled" : ""}>${esc(t.back)}</button>
          <button class="btn" id="next">${esc(i === r.steps.length - 1 ? t.done : t.next)}</button></div>`;
      $("#cx", el).onclick = close;
      $("#prev", el).onclick = () => { if (i > 0) { hardStop(); i--; draw(); } };
      $("#next", el).onclick = () => { hardStop(); if (i < r.steps.length - 1) { i++; draw(); } else { close(); location.href = r.doneUrl; } };
      const go = $("#tgo", el);
      if (go) go.onclick = () => {
        if (ringing) { stopAlarm(); draw(); return; }
        if (endAt) { left = remaining(); endAt = 0; clearTimer(); saveT(null); stopKeep(); draw(); return; }
        unlock();
        endAt = Date.now() + (left || s.minutes * 60) * 1000;
        saveT({ id: r.id, i, endAt });
        loop(); draw();
      };
    };
    draw();
    if (endAt) { unlock(); loop(); tick(); }
  };
  cookBtn.addEventListener("click", () => open());
  const sv = readT();
  if (sv && sv.id === r.id && Date.now() - sv.endAt < 6 * 3600 * 1000) open(sv.i, sv.endAt);
}
