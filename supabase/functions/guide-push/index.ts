// Schedules and sends Web Push "timer is up" notifications for the ATARIA guide.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";
import webpush from "npm:web-push@3.6.7";

const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
const ORIGINS = ["https://ataria-guide.vercel.app", "http://localhost:4173"];
const HOSTS = [".googleapis.com", ".push.services.mozilla.com", ".push.apple.com", ".notify.windows.com"];

const cors = (req: Request) => ({
  "Access-Control-Allow-Origin": ORIGINS.includes(req.headers.get("origin") ?? "") ? req.headers.get("origin")! : ORIGINS[0],
  "Access-Control-Allow-Headers": "content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Vary": "Origin",
});
const json = (req: Request, body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors(req), "Content-Type": "application/json" } });

const okEndpoint = (e: unknown) => {
  try { const u = new URL(String(e)); return u.protocol === "https:" && HOSTS.some((h) => u.hostname.endsWith(h)); } catch { return false; }
};

async function vapid() {
  const { data } = await db.from("guide_push_config").select("key,value");
  const m = Object.fromEntries((data ?? []).map((r) => [r.key, r.value]));
  webpush.setVapidDetails("https://ataria-guide.vercel.app", m.vapid_public, m.vapid_private);
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: cors(req) });
  const action = new URL(req.url).searchParams.get("action");

  if (action === "dispatch") {
    await vapid();
    const { data: due } = await db.from("guide_timers").select("id").eq("sent", false).lte("fire_at", new Date().toISOString()).limit(50);
    if (!due?.length) return json(req, { sent: 0 });
    const { data: rows } = await db.from("guide_timers").update({ sent: true }).in("id", due.map((d) => d.id)).eq("sent", false).select();
    let sent = 0;
    await Promise.all((rows ?? []).map(async (r) => {
      try {
        await webpush.sendNotification(r.sub, JSON.stringify({ title: r.title, body: r.body, url: r.url }), { TTL: 600, urgency: "high" });
        sent++;
      } catch (e) {
        await db.from("guide_timers").update({ error: String((e as { statusCode?: number }).statusCode ?? e).slice(0, 200) }).eq("id", r.id);
      }
    }));
    return json(req, { sent });
  }

  if (req.method !== "POST") return json(req, { error: "method" }, 405);
  let b: Record<string, any>;
  try { b = await req.json(); } catch { return json(req, { error: "json" }, 400); }

  if (action === "schedule") {
    const sub = b.sub, secs = Number(b.seconds);
    if (!sub || !okEndpoint(sub.endpoint) || !sub.keys?.p256dh || !sub.keys?.auth) return json(req, { error: "sub" }, 400);
    if (!(secs >= 5 && secs <= 5400)) return json(req, { error: "seconds" }, 400);
    await db.from("guide_timers").delete().eq("endpoint", sub.endpoint).eq("sent", false);
    const { error } = await db.from("guide_timers").insert({
      endpoint: sub.endpoint, sub,
      fire_at: new Date(Date.now() + secs * 1000).toISOString(),
      title: String(b.title ?? "ATARIA").slice(0, 80), body: String(b.body ?? "").slice(0, 200),
      url: String(b.url ?? "/").startsWith("https://ataria-guide.vercel.app/") ? String(b.url) : "/",
    });
    return json(req, error ? { error: "db" } : { ok: true }, error ? 500 : 200);
  }

  if (action === "cancel") {
    if (!okEndpoint(b.endpoint)) return json(req, { error: "endpoint" }, 400);
    await db.from("guide_timers").delete().eq("endpoint", b.endpoint).eq("sent", false);
    return json(req, { ok: true });
  }
  return json(req, { error: "action" }, 400);
});
