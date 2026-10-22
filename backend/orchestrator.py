"""Main agent (Jarvis): talks to the user, owns the workspace, delegates to sub-agents."""
from datetime import datetime, timedelta, timezone

import config
import db
import memory
import kaspi
from agents import data, research
from agents.runner import run_agent

SYSTEM = """Ты Jarvis, голосовой ИИ-помощник Алишера. Говоришь по-русски, коротко и живо, как в разговоре: \
без списков и markdown, одной-двумя фразами, если не просят подробнее.
Сегодня {today} (время Алматы). Текущий бизнес (workspace): {workspace}. Доступные: {workspaces}.
Что ты знаешь об Алишере и его целях:
{context}
Свежая сводка Kaspi по дням (без отмен и самовыкупов; на вопросы о заказах и выручке отвечай сразу из неё, без инструментов):
{kaspi}
Правила:
- Заказы и выручку за последние дни бери из сводки выше. Прибыль, себестоимость и комиссию Kaspi считай сам \
инструментами kaspi_profit, set_product_cost, set_kaspi_fee_percent. Сложные расчёты и анализ передавай в ask_data_agent.
- На вопрос «что сделал Claude / разработчик» вызывай developer_updates и перескажи коротко.
- Задачи и напоминания Алишера: add_task, list_tasks, complete_task. Даты в формате ГГГГ-ММ-ДД.
- «Что пишут в WhatsApp/Директ»: inbox. Клиентам сам не отвечай: предложи текст ответа, отправка только после «да» Алишера.
- Поиск в интернете (рынок, конкуренты, цены, ниши, поставщики, новости): ask_research, сформулируй вопрос подробно.
- Важное о предпочтениях и уроках сохраняй через remember; перед задачей при необходимости вспоминай через recall.
- Ничего необратимого (отправка сообщений, платежи, удаление) без прямого «да» от Алишера. Сообщения только черновиками.
- Если Алишер просит изменить, добавить или исправить что-то в самой системе Jarvis (новая функция, агент, подключение, голос, расчёт), \
запиши это через request_development: подробно, со всем, что он сказал. Скажи, что записал задачу разработчику; без одобрения Алишера ничего не применяется.
- Не выдумывай данные: если инструмента нет, честно скажи, что этого пока не умеешь."""

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
        rows = kaspi.daily_sales(7)
        synced = kaspi.last_synced_at()
        when = ""
        if synced:
            t = datetime.fromisoformat(synced.replace("Z", "+00:00")) + timedelta(hours=5)
            when = f"Данные Kaspi обновлены в {t:%H:%M} (Алматы); называя цифры, говори это время.\n"
        ship_today, ship_later = kaspi_packaging()
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
    s = _session(session_id)
    slugs = db.workspace_slugs()

    def dispatch(name, args):
        if name == "switch_workspace":
            if args["slug"] not in slugs:
                return {"error": f"нет такого бизнеса, есть: {slugs}"}
            s["workspace"] = args["slug"]
            return {"workspace": args["slug"]}
        if name == "ask_data_agent":
            return {"answer": data.handle(s["workspace"], args["task"])}
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
    system = SYSTEM.format(workspace=s["workspace"], workspaces=", ".join(slugs), today=today,
                           context=memory.standing_context(s["workspace"]) or "- (пока ничего)",
                           kaspi=_kaspi_snapshot())
    reply = run_agent(system, TOOLS, dispatch, s["history"] + [{"role": "user", "content": text}],
                      model=config.ORCHESTRATOR_MODEL, max_tokens=500)
    s["history"] = (s["history"] + [{"role": "user", "content": text},
                                    {"role": "assistant", "content": reply}])[-20:]
    _save(session_id, s)
    db.log_action(s["workspace"], "orchestrator", "chat", {"text": text}, {"reply": reply})
    return reply
