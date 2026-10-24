// Motion-powered life for the site: reveal on scroll, staggered cards, hero entrance, soft parallax, button press.
// Everything is skipped for visitors who prefer reduced motion, and content stays visible without JavaScript.
(() => {
  const M = window.Motion;
  if (!M || matchMedia("(prefers-reduced-motion: reduce)").matches) { document.documentElement.classList.remove("anim"); return; }
  const { animate, inView, stagger, scroll } = M;
  const ease = [0.22, 1, 0.36, 1];

  // page entrance
  animate("main", { opacity: [0, 1] }, { duration: 0.5, ease });

  // hero: text lines slide up in sequence, photo drifts in
  const heroTxt = document.querySelectorAll(".hero-txt > *, .p-hero .txt > *");
  if (heroTxt.length) animate(heroTxt, { opacity: [0, 1], y: [24, 0] }, { delay: stagger(0.08), duration: 0.7, ease });
  const heroPh = document.querySelector(".hero-ph, .p-hero .ph");
  if (heroPh) animate(heroPh, { opacity: [0, 1], scale: [1.04, 1], y: [20, 0] }, { duration: 1, ease });

  // sections and grids reveal when scrolled into view
  document.querySelectorAll(".sec-head, .stage-txt, .vstage, .vtabs, .band, .review, .story, .specs, .steps, .parts, .note, .split, .meta-strip, .page-head, .faqs").forEach((el) => {
    if (el.closest(".hero, .p-hero")) return;
    el.style.opacity = 0;
    inView(el, () => { animate(el, { opacity: [0, 1], y: [28, 0] }, { duration: 0.7, ease }); }, { margin: "0px 0px -8% 0px" });
  });
  document.querySelectorAll(".grid, .tiles, .pick, .tasks, .speeds, .rsteps, .results, .scenes").forEach((wrap) => {
    const kids = [...wrap.children];
    kids.forEach((k) => (k.style.opacity = 0));
    inView(wrap, () => { animate(kids, { opacity: [0, 1], y: [30, 0] }, { delay: stagger(0.07), duration: 0.65, ease }); }, { margin: "0px 0px -6% 0px" });
  });

  // soft parallax on large photos
  document.querySelectorAll(".hero-ph img, .p-hero .ph img, .story .ph img, .cover img").forEach((img) => {
    scroll(animate(img, { y: [-14, 14] }, { ease: "linear" }), { target: img.parentElement, offset: ["start end", "end start"] });
  });

  // 3D tilt on the dark stage photo (follows the pointer)
  const tilt = document.getElementById("tilt");
  if (tilt && matchMedia("(pointer: fine)").matches) {
    const img = tilt.querySelector("img");
    tilt.addEventListener("pointermove", (e) => {
      const r = tilt.getBoundingClientRect(), x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5;
      animate(img, { rotateY: x * 9, rotateX: -y * 7 }, { duration: 0.3 });
    });
    tilt.addEventListener("pointerleave", () => animate(img, { rotateY: 0, rotateX: 0 }, { duration: 0.6, ease }));
  }

  // press feedback on buttons and cards
  document.querySelectorAll(".btn, .card, .tiles a, .pick-card, .tasks a, .speeds a").forEach((el) => {
    el.addEventListener("pointerdown", () => animate(el, { scale: 0.975 }, { duration: 0.12 }));
    ["pointerup", "pointerleave", "pointercancel"].forEach((ev) => el.addEventListener(ev, () => animate(el, { scale: 1 }, { duration: 0.35, ease })));
  });

  // menu drawer and search slide in
  const drawer = document.getElementById("drawer");
  if (drawer) new MutationObserver(() => { if (!drawer.hidden) { animate(drawer, { opacity: [0, 1] }, { duration: 0.2 }); animate(".drawer-in", { x: [60, 0] }, { duration: 0.35, ease }); } }).observe(drawer, { attributes: true, attributeFilter: ["hidden"] });
})();
