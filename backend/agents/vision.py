"""Vision agent: looks at a photo by public URL (own product, competitor, Instagram post) and gives a marketing read."""
from datetime import datetime, timedelta, timezone

import config
import db
from agents.runner import run_agent

SYSTEM = (
    "Ты агент «Фото и контент» бизнес-помощника Алишера (бренд Ataria: ортопедические подушки, кухонная техника, продажа на Kaspi, "
    "контент для Instagram). Смотри на изображение и отвечай по делу: что на фото, сильные и слабые стороны, "
    "подходит ли для карточки Kaspi или Instagram, что улучшить (свет, композиция, фон, текст), какие 2–3 идеи для похожего кадра. "
    "Если на фото подушка Ataria, сверяй форму: серый верх, белые боковины, бирка ATARIA. Коротко, по-русски, без воды."
)


def handle(workspace: str, image_url: str, question: str) -> str:
    if not image_url.startswith("https://"):
        return "Нужна прямая ссылка на изображение (https://)."
    content = [{"type": "image", "source": {"type": "url", "url": image_url}},
               {"type": "text", "text": question or "Разбери это фото."}]
    out = run_agent(SYSTEM, [], lambda n, a: {"error": f"unknown tool {n}"},
                    [{"role": "user", "content": content}], model=config.ANTHROPIC_MODEL, max_tokens=1200)
    db.log_action(workspace, "vision", "analyze", {"url": image_url, "question": question}, {"answer": out})
    return out
