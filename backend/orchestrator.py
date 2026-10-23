"""Main agent (Jarvis): talks to the user, owns the workspace, delegates to sub-agents."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import config
import db
import memory
import kaspi
import kaspi_market
import crm
import instagram
from agents import data, research, vision
from agents.runner import run_agent

SYSTEM = """Ты Jarvis, голосовой ИИ-помощник Алишера. Говоришь по-русски, коротко и живо, как в разговоре: \
без списков и markdown, одной-двумя фразами, если не просят подробнее.
Правила:
- Себестоимость, прибыль и маржа по товарам, прибыль месяца, деньги компании, платежи, закуп, партии, остатки, реклама, расходы, возвраты: \
бери из кабинета Алишера инструментом kaspi_cabinet (это его главный учёт Kaspi, цифры точные). Данные кабинета только читай, не меняй. \
Если updated_at старше 12 часов, скажи, на какую дату цифры, и что они обновятся, когда Алишер откроет кабинет.
- Заказы и выручку за последние дни бери из сводки выше. Прибыль, себестоимость и комиссию Kaspi считай сам \
инструментами kaspi_profit, set_product_cost, set_kaspi_fee_percent. Сложные расчёты и анализ передавай в ask_data_agent.
- На вопрос «что сделал Claude / разработчик» вызывай developer_updates и перескажи коротко.
- Задачи и напоминания Алишера: add_task, list_tasks, complete_task. Даты в формате ГГГГ-ММ-ДД.
- «Что пишут в WhatsApp/Директ»: inbox. Клиентам сам не отвечай: предложи текст ответа, отправка только после «да» Алишера.
- Цены конкурентов, рынок и ниши на Kaspi: kaspi_search (и kaspi_offers для продавцов товара). Товары Ataria: подушки 35x60/40x60/40x61, комбайн AT-SM23, измельчители AT-1100/1700/2300.
- Тренды и идеи: для вопросов про тренды в мире, СНГ и Казахстане используй ask_research, проси сравнить три уровня \
(мир, СНГ, Казахстан), указать даты источников и в конце предложить 3 конкретные идеи для Ataria (товар, контент, реклама). \
Находки сохраняй через remember (kind=fact). Фото по ссылке разбирай через analyze_image.
- Поиск в интернете (рынок, конкуренты, цены, ниши, поставщики, новости): ask_research, сформулируй вопрос подробно.
- Важное о предпочтениях и уроках сохраняй через remember; перед задачей при необходимости вспоминай через recall.
- Поиск креаторов и клиентов: найди через ask_research, каждого запиши add_contact (ник, платформа, подписчики, цена, почему подходит), \
текст сообщения сохрани draft_message. Показывай Алишеру черновики и отправляй только после его «да».
- Утренний разговор: после приветствия Алишер называет цели на сегодня. Каждую цель сразу запиши add_task (due = сегодня), \
коротко подтверди и спроси, что ещё. Если он просит добавить или уточнить цифры, бери их из kaspi_cabinet или kaspi_profit. \
Если он просит напомнить вчерашнее или сравнить дни, используй сводку Kaspi выше.
- Ничего необратимого (отправка сообщений, платежи, удаление) без прямого «да» от Алишера. Сообщения только черновиками.
- Если Алишер просит изменить, добавить или исправить что-то в самой системе Jarvis (новая функция, агент, подключение, голос, расчёт), \
запиши это через request_development: подробно, со всем, что он сказал. Скажи, что записал задачу разработчику; без одобрения Алишера ничего не применяется.
- Если Алишер просит то, чего у тебя нет (фото, видео, монтаж, отправка в WhatsApp или Instagram, автоответчик Kaspi), честно скажи, что сам это пока не делаешь, \
и сразу запиши request_development с подробностями. Не отказывай молча.
- Как идут продажи, что просело, где слабая маржа или реклама, что улучшить на Kaspi: kaspi_analytics, потом конкретный совет с цифрами. \
Как идёт Instagram, какие посты зашли: instagram_stats.
- Любой вопрос про интернет, новости, цены, тренды, конкурентов, «найди», «что сейчас» решай сам инструментом web_search, \
не отправляй такие вопросы дальше. Глубокие многошаговые исследования отдавай ask_research.
- Отвечай сразу и коротко: на простое не вызывай инструменты, цифры дня бери из сводки ниже, несколько независимых инструментов вызывай одновременно.
- Не выдумывай данные: если инструмента нет, честно скажи, что этого пока не умеешь."""

DYNAMIC = """Сегодня {today} (время Алматы). Текущий бизнес (workspace): {workspace}. Доступные: {workspaces}.
Что ты знаешь об Алишере и его целях:
{context}
Свежая сводка Kaspi по дням (без отмен и самовыкупов; на вопросы о заказах и выручке отвечай сразу из неё, без инструментов):
{kaspi}"""

TOOLS = [
    {"name": "switch_workspace", "description": "Переключиться на другой бизнес.",
     "input_schema": {"type": "object", "properties": {"slug": {"type": "string"}}, "required": ["slug"]}},
    {"name": "ask_data_agent", "description": "Поручить расчёт или работу с цифрами агенту «Данные и расчёты».",
     "input_schema": {"type": "object", "properties": {"task": {"type": "string"}}, "required": ["task"]}},
    {"name": "request_development", "description": "Записать задачу на доработку самой системы Jarvis. Её возьмёт в работу разработчик (Claude Code).",
     "input_schema": {"type": "object", "properties": {
         "title": {"type": "string", "description": "Короткое название"},
         "details": {"type": "string", "description": "Что именно нужно, со всеми подробностями из слов Алишера"}},
         "required": ["title", "details"]}},
    {"name": "list_development_requests", "description": "Показать последние задачи на доработку системы и их статус.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "kaspi_cabinet", "description": "Цифры из «Ataria кабинет» (главный учёт Kaspi): без раздела — сводка по товарам, прибыль месяца, деньги; "
     "или один раздел подробно.",
     "input_schema": {"type": "object", "properties": {"section": {"type": "string", "enum": list(kaspi.CABINET_SECTIONS)}}}},
    *[t for t in data.TOOLS if t["name"] in ("kaspi_profit", "set_product_cost", "set_kaspi_fee_percent")],
    {"name": "developer_updates", "description": "Последние итоги работы разработчика (Claude Code) над системой.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "add_task", "description": "Записать задачу или напоминание Алишера.",
     "input_schema": {"type": "object", "properties": {
         "title": {"type": "string"}, "due": {"type": "string", "description": "ГГГГ-ММ-ДД, если назван срок"},
         "details": {"type": "string"}}, "required": ["title"]}},
    {"name": "list_tasks", "description": "Открытые задачи Алишера (по умолчанию все; due_until = до этой даты включительно).",
     "input_schema": {"type": "object", "properties": {"due_until": {"type": "string"}}}},
    {"name": "complete_task", "description": "Отметить задачу выполненной (по части названия).",
     "input_schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}},
    {"name": "ask_research", "description": "Исследование в интернете: рынок Казахстана, конкуренты, цены, ниши, поставщики. Занимает до минуты.",
     "input_schema": {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]}},
    {"name": "kaspi_search", "description": "Поиск товаров на Kaspi (Алматы): цены, рейтинг, число отзывов. Для конкурентов, ниш и рынка.",
     "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
    {"name": "kaspi_offers", "description": "Продавцы и их цены по конкретному товару Kaspi (id из kaspi_search).",
     "input_schema": {"type": "object", "properties": {"product_id": {"type": "string"}}, "required": ["product_id"]}},
    {"name": "add_contact", "description": "Записать в базу контактов человека: UGC-креатор, лид, поставщик, блогер.",
     "input_schema": {"type": "object", "properties": {
         "name": {"type": "string"}, "platform": {"type": "string", "description": "instagram, tiktok, whatsapp, telegram, 1688..."},
         "handle": {"type": "string"}, "phone": {"type": "string"}, "email": {"type": "string"},
         "source": {"type": "string", "description": "где нашёл"}, "notes": {"type": "string", "description": "подписчики, цены, ниша, почему подходит"}},
         "required": ["name"]}},
    {"name": "list_contacts", "description": "Показать базу контактов (фильтр по статусу new/contacted/replied/won/lost или по слову).",
     "input_schema": {"type": "object", "properties": {"status": {"type": "string"}, "query": {"type": "string"}}}},
    {"name": "update_contact", "description": "Сменить статус контакта или заметку (по имени или нику).",
     "input_schema": {"type": "object", "properties": {"who": {"type": "string"},
         "status": {"type": "string", "enum": ["new", "contacted", "replied", "won", "lost", "blocked"]}, "notes": {"type": "string"}},
         "required": ["who"]}},
    {"name": "draft_message", "description": "Сохранить ЧЕРНОВИК сообщения контакту. Ничего не отправляется.",
     "input_schema": {"type": "object", "properties": {"who": {"type": "string"}, "channel": {"type": "string"},
         "body": {"type": "string"}}, "required": ["who", "channel", "body"]}},
    {"name": "list_drafts", "description": "Черновики сообщений, которые ждут решения Алишера.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "analyze_image", "description": "Разобрать фото по ссылке: свои товары, конкуренты, посты Instagram. Что хорошо, что улучшить, идеи для похожего кадра.",
     "input_schema": {"type": "object", "properties": {"image_url": {"type": "string", "description": "прямая https-ссылка на картинку"},
         "question": {"type": "string"}}, "required": ["image_url"]}},
    {"name": "kaspi_analytics", "description": "Аналитика Kaspi: продажи и прибыль за период против прошлого такого же, падения продаж, слабая маржа, доля рекламы, по товарам.",
     "input_schema": {"type": "object", "properties": {"days": {"type": "integer", "description": "длина периода в днях, по умолчанию 7"}}}},
    {"name": "instagram_stats", "description": "Статистика Instagram @ataria.kz: подписчики и посты за период с охватом, просмотрами, сохранениями. Лучшие посты первыми.",
     "input_schema": {"type": "object", "properties": {"days": {"type": "integer"}}}},
    {"name": "whatsapp_clicks", "description": "Сколько людей перешли в WhatsApp по ссылке из Instagram (из био, роликов, рекламы), по источникам.",
     "input_schema": {"type": "object", "properties": {"days": {"type": "integer"}}}},
    {"name": "inbox", "description": "Последние входящие сообщения из WhatsApp и Instagram Direct.",
     "input_schema": {"type": "object", "properties": {"limit": {"type": "integer"}}}},
    {"name": "remember", "description": "Запомнить предпочтение, факт, урок или навык.",
     "input_schema": {"type": "object", "properties": {
         "kind": {"type": "string", "enum": list(memory.KINDS)}, "content": {"type": "string"},
         "shared": {"type": "boolean", "description": "true = помнить во всех бизнесах"}},
         "required": ["kind", "content"]}},
    {"name": "recall", "description": "Найти в памяти записи по слову или фразе (пусто = последние).",
     "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}}},
]

TOOLS.append({
    "type": "web_search_20260209", "name": "web_search", "max_uses": 2,
    "user_location": {"type": "approximate", "country": "KZ", "city": "Almaty", "timezone": "Asia/Almaty"},
})


def _session(session_id: str) -> dict:
    """Stored in the DB so any server instance (serverless or not) can continue the dialog."""
    rows = db.client().table("sessions").select("workspace,history").eq("session_id", session_id).execute().data
    if rows:
        return {"workspace": rows[0]["workspace"], "history": rows[0]["history"] or []}
    return {"workspace": config.DEFAULT_WORKSPACE, "history": []}


def _save(session_id: str, s: dict):
    db.client().table("sessions").upsert({
        "session_id": session_id, "workspace": s["workspace"], "history": s["history"],
        "updated_at": "now()",
    }).execute()


def _kaspi_day(dt_utc: datetime) -> "date":
    """Kaspi shipping day: orders after 16:00 Almaty ship the next day."""
    return (dt_utc + timedelta(hours=5) + timedelta(hours=8)).date()


def kaspi_packaging():
    """Orders in packaging split into today's shipment and the next day's (created after 16:00)."""
    today = (datetime.now(timezone.utc) + timedelta(hours=5)).date()
    ship_today, ship_later = [], []
    for o in kaspi.open_orders():
        day = _kaspi_day(datetime.fromisoformat(o["created_at"].replace("Z", "+00:00")))
        (ship_today if day <= today else ship_later).append(o)
    return ship_today, ship_later


def _kaspi_snapshot() -> str:
    try:
        now = datetime.now(timezone.utc)
        today = (now + timedelta(hours=5)).date()  # calendar day in Almaty
        with ThreadPoolExecutor(max_workers=3) as pool:
            f_rows = pool.submit(kaspi.daily_sales, 7)
            f_sync = pool.submit(kaspi.last_synced_at)
            f_pack = pool.submit(kaspi_packaging)
            rows, synced, (ship_today, ship_later) = f_rows.result(), f_sync.result(), f_pack.result()
        when = ""
        if synced:
            t = datetime.fromisoformat(synced.replace("Z", "+00:00")) + timedelta(hours=5)
            when = f"Данные Kaspi обновлены в {t:%H:%M} (Алматы); называя цифры, говори это время.\n"
        total = lambda xs: round(sum(float(x["total"] or 0) for x in xs))
        packaging = (
            f"СЕГОДНЯШНИЕ ЗАКАЗЫ (в упаковке, отгрузка сегодня {today}): {len(ship_today)} на {total(ship_today)} ₸. "
            f"Новые после 16:00, отгрузка завтра: {len(ship_later)} на {total(ship_later)} ₸. "
            "На «сколько заказов сегодня» называй сначала сегодняшние в упаковке, потом новые на завтра.\n")
        days = "\n".join(f"- день отгрузки {r['day']}: {r['orders']} заказов, {r['units']} шт, {round(float(r['revenue']))} ₸"
                         for r in rows)
        return (when + packaging + "Заказы по дням отгрузки Kaspi (созданные после 16:00 относятся к следующему дню; "
                "отменённые и самовыкупы не считаются):\n" + days)
    except Exception as e:
        return f"- (сводка недоступна: {type(e).__name__})"


def chat(session_id: str, text: str) -> str:
    with ThreadPoolExecutor(max_workers=3) as pool:
        f_session = pool.submit(_session, session_id)
        f_snapshot = pool.submit(_kaspi_snapshot)
        s = f_session.result()
        f_context = pool.submit(memory.standing_context, s["workspace"])
        slugs = db.workspace_slugs()
        snapshot, context = f_snapshot.result(), f_context.result()

    def dispatch(name, args):
        if name == "switch_workspace":
            if args["slug"] not in slugs:
                return {"error": f"нет такого бизнеса, есть: {slugs}"}
            s["workspace"] = args["slug"]
            return {"workspace": args["slug"]}
        if name == "ask_data_agent":
            return {"answer": data.handle(s["workspace"], args["task"])}
        if name == "kaspi_cabinet":
            return kaspi.cabinet(args.get("section"))
        if name == "kaspi_profit":
            return kaspi.profit(args["date_from"], args["date_to"], args.get("include_partner", False))
        if name == "set_product_cost":
            return kaspi.set_cost(args["product"], float(args["unit_cost"]))
        if name == "set_kaspi_fee_percent":
            return kaspi.set_setting("kaspi_fee_percent", float(args["percent"]))
        if name == "developer_updates":
            return db.client().table("dev_log").select("summary,created_at").order("created_at", desc=True).limit(5).execute().data
        if name == "add_task":
            row = db.client().table("tasks").insert({
                "workspace_id": db.workspace_id(s["workspace"]), "title": args["title"], "agent": "alisher",
                "payload": {"due": args.get("due"), "details": args.get("details", "")},
            }).execute().data[0]
            return {"saved": row["id"]}
        if name == "list_tasks":
            rows = (db.client().table("tasks").select("title,payload,created_at").eq("agent", "alisher")
                    .eq("status", "todo").order("created_at").limit(50).execute().data)
            until = args.get("due_until")
            if until:
                rows = [r for r in rows if (r["payload"] or {}).get("due") and r["payload"]["due"] <= until]
            return [{"title": r["title"], "due": (r["payload"] or {}).get("due"),
                     "details": (r["payload"] or {}).get("details")} for r in rows]
        if name == "complete_task":
            rows = (db.client().table("tasks").select("id,title").eq("agent", "alisher").eq("status", "todo")
                    .ilike("title", f"%{args['title'].strip()}%").execute().data)
            if len(rows) != 1:
                return {"matches": [r["title"] for r in rows], "hint": "уточни, какую именно задачу"}
            db.client().table("tasks").update({"status": "done"}).eq("id", rows[0]["id"]).execute()
            return {"done": rows[0]["title"]}
        if name == "ask_research":
            return {"answer": research.handle(s["workspace"], args["question"])}
        if name == "kaspi_search":
            return kaspi_market.search(args["text"])
        if name == "kaspi_offers":
            return kaspi_market.offers(args["product_id"])
        if name == "add_contact":
            return crm.add_contact(s["workspace"], **args)
        if name == "list_contacts":
            return crm.list_contacts(s["workspace"], args.get("status"), args.get("query"))
        if name == "update_contact":
            return crm.update_contact(s["workspace"], args["who"], args.get("status"), args.get("notes"))
        if name == "draft_message":
            return crm.draft_message(s["workspace"], args["who"], args["channel"], args["body"])
        if name == "list_drafts":
            return crm.list_drafts(s["workspace"])
        if name == "analyze_image":
            return {"answer": vision.handle(s["workspace"], args["image_url"], args.get("question", ""))}
        if name == "kaspi_analytics":
            return kaspi.analytics(args.get("days", 7))
        if name == "instagram_stats":
            return instagram.stats(args.get("days", 30))
        if name == "whatsapp_clicks":
            return crm.link_clicks(args.get("days", 7))
        if name == "inbox":
            import meta  # local import: meta imports orchestrator
            return meta.inbox(args.get("limit", 15))
        if name == "request_development":
            row = db.client().table("improvement_proposals").insert({
                "workspace_id": db.workspace_id(s["workspace"]),
                "title": args["title"][:200], "description": args["details"],
            }).execute().data[0]
            return {"saved": row["id"], "status": "proposed",
                    "say": "Записал. Разработчик проверяет очередь раз в час, о готовности скажу в начале разговора."}
        if name == "list_development_requests":
            return db.client().table("improvement_proposals").select("title,status,created_at") \
                .order("created_at", desc=True).limit(10).execute().data
        if name == "remember":
            return memory.remember(s["workspace"], args["kind"], args["content"], args.get("shared", False))
        if name == "recall":
            return memory.recall(s["workspace"], args.get("query", ""))
        raise ValueError(f"unknown tool {name}")

    today = (datetime.now(timezone.utc) + timedelta(hours=5)).date()
    system = [{"type": "text", "text": SYSTEM},
              {"type": "text", "text": DYNAMIC.format(workspace=s["workspace"], workspaces=", ".join(slugs), today=today,
                                                      context=context or "- (пока ничего)", kaspi=snapshot)}]
    reply = run_agent(system, TOOLS, dispatch, s["history"] + [{"role": "user", "content": text}],
                      model=config.ORCHESTRATOR_MODEL, max_tokens=500)
    s["history"] = (s["history"] + [{"role": "user", "content": text},
                                    {"role": "assistant", "content": reply}])[-20:]
    with ThreadPoolExecutor(max_workers=2) as pool:  # save and log side by side
        futs = [pool.submit(_save, session_id, s),
                pool.submit(db.log_action, s["workspace"], "orchestrator", "chat", {"text": text}, {"reply": reply})]
        for f in futs:
            try:
                f.result()
            except Exception as e:
                print(f"post-chat write failed: {type(e).__name__}")
    return reply
