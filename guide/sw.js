// Needed so the timer can show a "time is up" notification.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));
self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || "/";
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((cs) => {
    for (const c of cs) if ("focus" in c) return c.focus();
    return self.clients.openWindow(url);
  }));
});

// Web Push from the server: shown when the timer ends and the page is not open in front of the user.
self.addEventListener("push", (e) => {
  let d = {};
  try { d = e.data.json(); } catch (err) { d = { title: "ATARIA", body: e.data ? e.data.text() : "" }; }
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((cs) => {
    if (cs.some((c) => c.visibilityState === "visible")) return;
    return self.registration.showNotification(d.title || "ATARIA", {
      body: d.body || "", tag: "ataria-timer", requireInteraction: true, vibrate: [300, 150, 300, 150, 300],
      icon: "/img/icon-192.png", data: { url: d.url || "/" },
    });
  }));
});
