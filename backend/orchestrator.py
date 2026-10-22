"""Main agent (Jarvis): talks to the user, owns the workspace, delegates to sub-agents."""
import config
import db
import memory
from agents import data
from agents.runner import run_agent

SYSTEM = """Ты Jarvis, голосовой ИИ-помощник Алишера. Говоришь по-русски, коротко и живо, как в разговоре: \
без списков и markdown, одной-двумя фразами, если не просят подробнее.
Текущий бизнес (workspace): {workspace}. Доступные: {workspaces}.
Правила:
- Любые расчёты и работу с цифрами передавай агенту через ask_data_agent.
- Важное о предпочтениях и уроках сохраняй через remember; перед задачей при необходимости вспоминай через recall.
- Ничего необратимого (отправка сообщений, платежи, удаление) без прямого «да» от Алишера. Сообщения только черновиками.
- Не выдумывай данные: если инструмента нет, честно скажи, что этого пока не умеешь."""

TOOLS = [
    {"name": "switch_workspace", "description": "Переключиться на другой бизнес.",
     "input_schema": {"type": "object", "properties": {"slug": {"type": "string"}}, "required": ["slug"]}},
    {"name": "ask_data_agent", "description": "Поручить расчёт или работу с цифрами агенту «Данные и расчёты».",
     "input_schema": {"type": "object", "properties": {"task": {"type": "string"}}, "required": ["task"]}},
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
        if name == "remember":
            return memory.remember(s["workspace"], args["kind"], args["content"], args.get("shared", False))
        if name == "recall":
            return memory.recall(s["workspace"], args.get("query", ""))
        raise ValueError(f"unknown tool {name}")

    system = SYSTEM.format(workspace=s["workspace"], workspaces=", ".join(slugs))
    reply = run_agent(system, TOOLS, dispatch, s["history"] + [{"role": "user", "content": text}])
    s["history"] = (s["history"] + [{"role": "user", "content": text},
                                    {"role": "assistant", "content": reply}])[-20:]
    _save(session_id, s)
    db.log_action(s["workspace"], "orchestrator", "chat", {"text": text}, {"reply": reply})
    return reply
