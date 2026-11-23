// «Финансы» — умный ввод. Текст (в том числе надиктованный) и фото/PDF чеков -> операции в public.fin_transactions.
// Работает от имени вошедшего пользователя: все чтения и записи идут через его JWT и политики RLS.
// Быстрые команды iPhone (Apple Pay, «Поделиться» из Kaspi) приходят без входа: с ключом устройства в заголовке
// x-fin-token. Ключ хранится в fin_device_tokens только как SHA-256; при совпадении функция работает с правами сервиса.
// Секреты: ANTHROPIC_API_KEY (уже есть в проекте). SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY даёт платформа.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import Anthropic from "npm:@anthropic-ai/sdk";
import { createClient } from "npm:@supabase/supabase-js@2";

const env = (k: string) => (Deno.env.get(k) ?? "").trim();
const claude = new Anthropic({ apiKey: env("ANTHROPIC_API_KEY") });
const MODEL = "claude-opus-5-5";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-fin-token",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...CORS, "Content-Type": "application/json" } });

const SYSTEM = `Ты бухгалтер-помощник Алишера (Казахстан, валюта тенге ₸). Он пишет или надиктовывает голосом короткие сообщения о деньгах, иногда прикладывает фото или PDF чека. Твоя задача: превратить сообщение в операции учёта и коротко ответить.

Правила:
- Каждая отдельная трата, доход или перевод — отдельная операция. «Потратил 5 тысяч на такси и 12 на обед» — две операции.
- Суммы в тенге. «5к», «5 тыщ», «пять тысяч» = 5000. «1,2 млн» = 1200000. Валюта не тенге — пересчитай по примерному курсу и напиши курс в note.
- Дата: «сегодня» по умолчанию; «вчера», «позавчера», «в понедельник», «15-го» считай от сегодняшней даты. В будущее не ставь.
- Счёт выбирай из списка. «Каспи», «голд», «с карты» = kaspi-gold; «со счёта компании», «с бизнес-счёта», «Kaspi Pay», «с ИП» = kaspi-pay (это счёт компании); «наличкой», «налом» = cash; «депозит» = kaspi-deposit. Не сказано — kaspi-gold для личного и kaspi-pay для бизнеса.
- Проект: подушки -> pillows, комбайн / SM23 -> combines, измельчители / AT-2300 / AT-1700 / AT-1100 -> choppers, реклама, таргет, блогеры, UGC -> ads, общее по бизнесу -> business, всё личное (еда, такси, жильё, одежда, развлечения) -> personal.
- Категорию выбирай только из списка, точным названием. Не подходит ни одна — «Прочее» (для расхода) или «Прочий доход».
- Перевод между своими счетами (снял наличные, перевёл с Pay на Gold, положил на депозит) — type "transfer", to_account_slug обязателен, project и category = null.
- Компания Ataria (подушки, комбайны, измельчители, реклама, карго, склад) ведёт свой учёт в «кабинете» (поле company в контексте: деньги компании, её расходы, платежи заводу, долги компании Алишеру). Расход на бизнес помечай company=true: он уйдёт в кабинет. Если бизнес-расход оплачен с личной карты или наличными, счёт личный, company=true (тогда компания должна Алишеру). Личные траты: company=false.
- Не дублируй кабинет: если такая трата или платёж уже есть в company.expenses или company.upcoming (та же сумма и близкая дата или то же описание), не записывай её, а скажи в reply, что она уже учтена в кабинете.
- Вопросы про компанию (сколько денег у компании, прибыль за месяц, долг компании мне, что платить заводу) отвечай по полю company.
- Продажи Kaspi НЕ записывай: они подтягиваются автоматически. Поступления от Kaspi на счёт тоже не записывай как доход.
- «Оплата Apple Pay: <магазин>, <сумма>, карта <название>» приходит автоматически после оплаты телефоном: это расход с той карты (Kaspi Gold -> kaspi-gold), категорию и проект определи по магазину, в note — магазин.
- «Куда: <раздел>» в сообщении — это выбор самого Алишера, он главнее твоих догадок. «Личное» -> project personal, company=false. «Подушки», «Комбайны», «Измельчители», «Реклама», «Бизнес — общее» -> этот проект, company=true. Без «Куда:» оплата Apple Pay считается личной.
- Чек: возьми итоговую сумму к оплате, дату с чека, магазин и главное в note. Если на чеке разные по смыслу позиции (например, продукты и бытовая химия), можно разбить по категориям, но сумма должна сойтись с итогом.
- «На Kaspi Gold сейчас 245 000», «остаток на депозите 3 млн» — это balance_updates, не операция.
- Если сообщение — вопрос («сколько я потратил на рекламу?»), ничего не записывай, ответь в reply по данным из контекста.
- Если не уверен в сумме или смысле, не выдумывай: не записывай эту часть и переспроси в reply.
- reply — 1–3 коротких предложения на русском: что записано (сумма, счёт, проект) или ответ на вопрос. Без markdown.`;

type Acc = { id: string; slug: string; name: string; kind: string; balance: number; archived: boolean; balance_source: string };
type Proj = { id: string; slug: string; name: string; archived: boolean };
type Cat = { id: string; name: string; type: string };

function schema(accSlugs: string[], projSlugs: string[], catNames: string[]) {
  const nullable = (s: Record<string, unknown>) => ({ anyOf: [s, { type: "null" }] });
  return {
    type: "object",
    additionalProperties: false,
    required: ["reply", "transactions", "balance_updates"],
    properties: {
      reply: { type: "string" },
      transactions: {
        type: "array",
        items: {
          type: "object",
          additionalProperties: false,
          required: ["type", "amount", "occurred_on", "account_slug", "to_account_slug", "project_slug", "category_name", "note", "company"],
          properties: {
            type: { type: "string", enum: ["expense", "income", "transfer"] },
            amount: { type: "number", description: "Сумма в тенге, больше нуля" },
            occurred_on: { type: "string", format: "date" },
            account_slug: { type: "string", enum: accSlugs },
            to_account_slug: nullable({ type: "string", enum: accSlugs }),
            project_slug: nullable({ type: "string", enum: projSlugs }),
            category_name: nullable({ type: "string", enum: catNames }),
            note: nullable({ type: "string" }),
            company: { type: "boolean", description: "true, если это расход или доход компании Ataria" },
          },
        },
      },
      balance_updates: {
        type: "array",
        items: {
          type: "object",
          additionalProperties: false,
          required: ["account_slug", "balance"],
          properties: { account_slug: { type: "string", enum: accSlugs }, balance: { type: "number" } },
        },
      },
    },
  };
}

async function sha256(s: string): Promise<string> {
  const h = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)));
  return Array.from(h, (b) => b.toString(16).padStart(2, "0")).join("");
}

function b64(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf);
  let s = "";
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(s);
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ error: "method not allowed" }, 405);

  const url = new URL(req.url);
  const deviceToken = (req.headers.get("x-fin-token") ?? url.searchParams.get("token") ?? "").trim();
  let db;
  let source = "app-ai";
  if (deviceToken) {
    // iPhone Shortcut: check the device key, then act for the owner with the service role
    const admin = createClient(env("SUPABASE_URL"), env("SUPABASE_SERVICE_ROLE_KEY"), { auth: { persistSession: false } });
    const hash = await sha256(deviceToken);
    const { data: tok } = await admin.from("fin_device_tokens").select("token_hash").eq("token_hash", hash).maybeSingle();
    if (!tok) return json({ error: "Неверный ключ устройства" }, 403);
    await admin.from("fin_device_tokens").update({ last_used_at: new Date().toISOString() }).eq("token_hash", hash);
    db = admin;
    source = "shortcut";
  } else {
    db = createClient(env("SUPABASE_URL"), env("SUPABASE_ANON_KEY"), {
      global: { headers: { Authorization: req.headers.get("Authorization") ?? "" } },
      auth: { persistSession: false },
    });
    const { data: owner } = await db.rpc("fin_is_owner");
    if (!owner) return json({ error: "Нет доступа" }, 403);
  }

  // JSON from the app; JSON or a form with a file from a Shortcut
  let body: { text?: string; files?: string[]; today?: string } = {};
  const uploaded: string[] = [];
  const ctype = req.headers.get("content-type") ?? "";
  try {
    if (ctype.includes("multipart/form-data")) {
      const form = await req.formData();
      body.text = String(form.get("text") ?? "");
      body.today = String(form.get("today") ?? "");
      for (const [, v] of form.entries()) {
        if (typeof v === "string" || uploaded.length >= 3) continue;
        const isPdf = v.type === "application/pdf" || v.name.toLowerCase().endsWith(".pdf");
        const isImg = ["image/jpeg", "image/png", "image/webp"].includes(v.type);
        if (!isPdf && !isImg) continue;
        const ext = isPdf ? "pdf" : v.type === "image/png" ? "png" : v.type === "image/webp" ? "webp" : "jpg";
        const path = `${new Date().toISOString().slice(0, 7)}/${crypto.randomUUID()}.${ext}`;
        const { error } = await db.storage.from("fin-receipts").upload(path, v, { contentType: isPdf ? "application/pdf" : v.type });
        if (!error) uploaded.push(path);
      }
    } else {
      body = await req.json();
    }
  } catch { return json({ error: "Не удалось прочитать запрос" }, 400); }
  const text = String(body.text ?? "").trim().slice(0, 4000);
  // a Shortcut may only send files it uploaded in this request
  const files = [...(source === "shortcut" ? [] : (body.files ?? [])).filter((p) => typeof p === "string"), ...uploaded].slice(0, 5);
  // Kazakhstan is UTC+5: a Shortcut sends no date, so use Almaty's calendar day
  const today = /^\d{4}-\d{2}-\d{2}$/.test(body.today ?? "") ? body.today! : new Date(Date.now() + 5 * 3600e3).toISOString().slice(0, 10);
  if (!text && !files.length) return json({ error: "Пустое сообщение" }, 400);

  const month = today.slice(0, 7);
  const [acc, proj, cat, recent, monthTx, kaspi, company] = await Promise.all([
    db.from("fin_account_balances").select("id,slug,name,kind,balance,archived,balance_source").order("sort"),
    db.from("fin_projects").select("id,slug,name,archived").order("sort"),
    db.from("fin_categories").select("id,name,type").order("sort"),
    db.from("fin_transactions").select("occurred_on,type,amount,account_id,to_account_id,project_id,category_id,note")
      .order("created_at", { ascending: false }).limit(15),
    db.from("fin_transactions").select("type,amount,project_id,category_id").gte("occurred_on", month + "-01"),
    db.rpc("fin_kaspi_monthly", { p_from: month + "-01" }),
    db.rpc("fin_company"),
  ]);
  for (const r of [acc, proj, cat]) if (r.error) return json({ error: r.error.message }, 500);
  const accounts = (acc.data as Acc[]).filter((a) => !a.archived);
  const projects = (proj.data as Proj[]).filter((p) => !p.archived);
  const categories = cat.data as Cat[];
  const accBy = (id: string | null) => accounts.find((a) => a.id === id)?.slug ?? null;
  const projBy = (id: string | null) => projects.find((p) => p.id === id)?.slug ?? null;
  const catBy = (id: string | null) => categories.find((c) => c.id === id)?.name ?? null;

  // month totals per project and category, for answering questions
  const byProj: Record<string, { income: number; expense: number }> = {};
  const byCat: Record<string, number> = {};
  for (const t of monthTx.data ?? []) {
    if (t.type === "transfer") continue;
    const p = projBy(t.project_id) ?? "без проекта";
    (byProj[p] ??= { income: 0, expense: 0 })[t.type as "income" | "expense"] += Number(t.amount);
    if (t.type === "expense") { const c = catBy(t.category_id) ?? "без категории"; byCat[c] = (byCat[c] ?? 0) + Number(t.amount); }
  }

  const context = {
    today,
    accounts: accounts.map((a) => ({ slug: a.slug, name: a.name, kind: a.kind, balance: Math.round(Number(a.balance)) })),
    projects: projects.map((p) => ({ slug: p.slug, name: p.name })),
    categories: { expense: categories.filter((c) => c.type === "expense").map((c) => c.name), income: categories.filter((c) => c.type === "income").map((c) => c.name) },
    this_month: { by_project: byProj, expenses_by_category: byCat, kaspi_sales: kaspi.data ?? [] },
    company: company.data ? {
      cash: company.data.cash, reserve: company.data.reserve, owner_debt_to_alisher: company.data.owner_debt,
      pnl_month: company.data.pnl_month, upcoming_payments: company.data.upcoming,
      expenses: (company.data.expenses ?? []).slice(-40), owner_loans: company.data.owner_loans,
    } : null,
    recent_transactions: (recent.data ?? []).map((t) => ({
      date: t.occurred_on, type: t.type, amount: Number(t.amount), account: accBy(t.account_id), to: accBy(t.to_account_id),
      project: projBy(t.project_id), category: catBy(t.category_id), note: t.note,
    })),
  };

  // attachments come from the private bucket; RLS lets only the owner read them
  const blocks: Anthropic.Beta.BetaContentBlockParam[] = [];
  for (const path of files) {
    const { data, error } = await db.storage.from("fin-receipts").download(path);
    if (error || !data) continue;
    const buf = await data.arrayBuffer();
    if (path.toLowerCase().endsWith(".pdf")) {
      blocks.push({ type: "document", source: { type: "base64", media_type: "application/pdf", data: b64(buf) } });
    } else {
      const mt = data.type === "image/png" ? "image/png" : data.type === "image/webp" ? "image/webp" : "image/jpeg";
      blocks.push({ type: "image", source: { type: "base64", media_type: mt, data: b64(buf) } });
    }
  }
  blocks.push({
    type: "text",
    text: `Контекст учёта (JSON):\n${JSON.stringify(context)}\n\nСообщение Алишера:\n${text || "(только вложение: это чек, запиши его)"}`,
  });

  const { data: inbox, error: inboxErr } = await db.from("fin_inbox").insert({ text: text || null, files, source }).select("id").single();
  if (inboxErr) return json({ error: inboxErr.message }, 500);

  let parsed: {
    reply: string;
    transactions: { type: string; amount: number; occurred_on: string; account_slug: string; to_account_slug: string | null; project_slug: string | null; category_name: string | null; note: string | null; company: boolean }[];
    balance_updates: { account_slug: string; balance: number }[];
  };
  try {
    const response = await claude.beta.messages.create({
      model: MODEL,
      max_tokens: 16000,
      betas: ["server-side-fallback-2026-07-01"],
      fallbacks: "default",
      output_config: {
        effort: "low",
        format: { type: "json_schema", schema: schema(accounts.map((a) => a.slug), projects.map((p) => p.slug), categories.map((c) => c.name)) },
      },
      system: SYSTEM,
      messages: [{ role: "user", content: blocks }],
    } as Anthropic.Beta.MessageCreateParamsNonStreaming);
    if (response.stop_reason === "refusal") throw new Error("Модель отказалась обработать сообщение");
    if (response.stop_reason === "max_tokens") throw new Error("Слишком длинный ответ, попробуйте разбить сообщение");
    const out = response.content.filter((b) => b.type === "text").map((b) => (b as Anthropic.Beta.BetaTextBlock).text).join("");
    parsed = JSON.parse(out);
  } catch (e) {
    const msg = e instanceof Anthropic.APIError ? `ИИ недоступен (${e.status})` : String((e as Error).message ?? e);
    await db.from("fin_inbox").update({ status: "error", reply: msg }).eq("id", inbox.id);
    return json({ error: msg }, 502);
  }

  const slugToAcc = (s: string | null) => (s ? accounts.find((a) => a.slug === s)?.id ?? null : null);
  const rows = parsed.transactions
    .filter((t) => t.amount > 0 && slugToAcc(t.account_slug))
    .filter((t) => t.type !== "transfer" || (slugToAcc(t.to_account_slug) && t.to_account_slug !== t.account_slug))
    .map((t) => ({
      type: t.type,
      amount: Math.round(t.amount * 100) / 100,
      occurred_on: t.occurred_on > today ? today : t.occurred_on,
      account_id: slugToAcc(t.account_slug),
      to_account_id: t.type === "transfer" ? slugToAcc(t.to_account_slug) : null,
      project_id: t.type === "transfer" ? null : projects.find((p) => p.slug === t.project_slug)?.id ?? null,
      category_id: t.type === "transfer" ? null
        : categories.find((c) => c.name === t.category_name && c.type === (t.type === "income" ? "income" : "expense"))?.id ?? null,
      note: t.note,
      source,
      company: t.type !== "transfer" && !!t.company,
      cabinet_status: t.type !== "transfer" && t.company ? "pending" : null,
      inbox_id: inbox.id,
      receipt_path: files[0] ?? null,
    }));

  let inserted: { id: string }[] = [];
  if (rows.length) {
    const r = await db.from("fin_transactions").insert(rows).select("*");
    if (r.error) {
      await db.from("fin_inbox").update({ status: "error", reply: r.error.message }).eq("id", inbox.id);
      return json({ error: r.error.message }, 500);
    }
    inserted = r.data;
  }

  // "на Kaspi Gold сейчас 245 000": move the account's starting point to today
  const balanceDone: { account: string; balance: number }[] = [];
  for (const u of parsed.balance_updates) {
    const a = accounts.find((x) => x.slug === u.account_slug);
    if (!a || a.balance_source === "cabinet") continue; // the company account's balance belongs to the cabinet
    const { data: todays } = await db.from("fin_transactions").select("type,amount,account_id,to_account_id")
      .eq("occurred_on", today).or(`account_id.eq.${a.id},to_account_id.eq.${a.id}`);
    let delta = 0;
    for (const t of todays ?? []) {
      if (t.account_id === a.id) delta += t.type === "income" ? Number(t.amount) : -Number(t.amount);
      if (t.to_account_id === a.id && t.type === "transfer") delta += Number(t.amount);
    }
    const { error } = await db.from("fin_accounts").update({ opening_balance: u.balance - delta, opening_date: today }).eq("id", a.id);
    if (!error) balanceDone.push({ account: a.name, balance: u.balance });
  }

  await db.from("fin_inbox").update({ reply: parsed.reply, transaction_ids: inserted.map((t) => t.id) }).eq("id", inbox.id);
  // a Shortcut shows the reply as a notification: plain text is easiest there
  if (url.searchParams.get("reply") === "text") return new Response(parsed.reply, { headers: { ...CORS, "Content-Type": "text/plain; charset=utf-8" } });
  return json({ inbox_id: inbox.id, reply: parsed.reply, transactions: inserted, balances: balanceDone });
});
