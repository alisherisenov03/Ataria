"""Research agent: live web search (market, competitors, suppliers), answers with sources."""
from datetime import datetime, timedelta, timezone

import config
import db
from agents.runner import run_agent

SYSTEM = (
    "Ты агент «Исследования» бизнес-помощника Алишера (Казахстан, товары на Kaspi: ортопедические подушки, "
    "кухонные измельчители и другое). Сегодня {today}. Ищи в интернете через web_search, сравнивай источники, "
    "давай конкретику: цены в тенге, названия, ссылки на источники (коротко, по названию сайта). "
    "Если данных нет или они ненадёжны, так и скажи. Ответ: 3–6 коротких пунктов, по-русски, без воды."
)

TOOLS = [{
    "type": "web_search_20260209", "name": "web_search", "max_uses": 3,
    "user_location": {"type": "approximate", "country": "KZ", "city": "Almaty", "timezone": "Asia/Almaty"},
}]


def handle(workspace: str, question: str) -> str:
    today = (datetime.now(timezone.utc) + timedelta(hours=5)).date()
    out = run_agent(SYSTEM.format(today=today), TOOLS, lambda name, args: {"error": f"unknown tool {name}"},
                    [{"role": "user", "content": question}], model=config.ANTHROPIC_MODEL, max_tokens=3000)
    db.log_action(workspace, "research", "question", {"question": question}, {"answer": out})
    return out
