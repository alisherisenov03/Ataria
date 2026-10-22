"""Data & calculations agent: numbers, saved calculations."""
import ast
import operator as op
from datetime import datetime, timedelta, timezone

import db
import kaspi
from agents.runner import run_agent

SYSTEM = (
    "Ты агент «Данные и расчёты». Считаешь точно: любое вычисление делай через инструмент calculate, "
    "не в уме. Важные расчёты сохраняй через save_calculation. Отвечай коротко, по-русски, с итоговыми числами.\n"
    "Сегодня {today} (Алматы), вчера {yesterday}. Даты для инструментов: ГГГГ-ММ-ДД.\n"
    "Прибыль Kaspi считай через kaspi_profit. Если у товаров нет себестоимости или не задана комиссия Kaspi, "
    "назови выручку и прямо скажи, каких данных не хватает (какие товары), чтобы Алишер их назвал. "
    "Себестоимость сохраняй через set_product_cost, комиссию через set_kaspi_fee_percent, только со слов Алишера."
)


def _almaty_today():
    return (datetime.now(timezone.utc) + timedelta(hours=5)).date()

TOOLS = [
    {"name": "calculate", "description": "Вычислить арифметическое выражение (+ - * / ** % //, скобки).",
     "input_schema": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}},
    {"name": "save_calculation", "description": "Сохранить расчёт в базу.",
     "input_schema": {"type": "object", "properties": {
         "title": {"type": "string"}, "inputs": {"type": "object"}, "result": {"type": "object"}},
         "required": ["title", "result"]}},
    {"name": "kaspi_daily_sales", "description": "Продажи Kaspi по дням (заказы, штуки, выручка в ₸, без отмен и самовыкупов).",
     "input_schema": {"type": "object", "properties": {"days": {"type": "integer"}}}},
    {"name": "kaspi_profit", "description": "Выручка, себестоимость, комиссия Kaspi и прибыль за период по товарам.",
     "input_schema": {"type": "object", "properties": {
         "date_from": {"type": "string"}, "date_to": {"type": "string"},
         "include_partner": {"type": "boolean", "description": "true = включить товары партнёра"}},
         "required": ["date_from", "date_to"]}},
    {"name": "set_product_cost", "description": "Сохранить себестоимость одной единицы товара (по коду или части названия).",
     "input_schema": {"type": "object", "properties": {
         "product": {"type": "string"}, "unit_cost": {"type": "number"}}, "required": ["product", "unit_cost"]}},
    {"name": "set_kaspi_fee_percent", "description": "Сохранить комиссию Kaspi в процентах от выручки.",
     "input_schema": {"type": "object", "properties": {"percent": {"type": "number"}}, "required": ["percent"]}},
    {"name": "list_calculations", "description": "Последние сохранённые расчёты.",
     "input_schema": {"type": "object", "properties": {"limit": {"type": "integer"}}}},
]

_OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv, ast.Mod: op.mod, ast.Pow: op.pow,
    ast.USub: op.neg, ast.UAdd: op.pos,
}


def calc(expression: str) -> float:
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return n.value
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.operand))
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Pow) and abs(b) > 100:
                raise ValueError("слишком большая степень")
            return _OPS[type(n.op)](a, b)
        raise ValueError("разрешены только числа и арифметика")
    return ev(ast.parse(expression.replace(",", ".").replace("^", "**"), mode="eval"))


def handle(workspace: str, task: str) -> str:
    def dispatch(name, args):
        if name == "calculate":
            return {"result": calc(args["expression"])}
        if name == "save_calculation":
            row = db.client().table("calculations").insert({
                "workspace_id": db.workspace_id(workspace), "title": args["title"],
                "inputs": args.get("inputs", {}), "result": args["result"],
            }).execute().data[0]
            return {"saved": row["id"]}
        if name == "kaspi_daily_sales":
            return kaspi.daily_sales(args.get("days", 14))
        if name == "kaspi_profit":
            return kaspi.profit(args["date_from"], args["date_to"], args.get("include_partner", False))
        if name == "set_product_cost":
            return kaspi.set_cost(args["product"], float(args["unit_cost"]))
        if name == "set_kaspi_fee_percent":
            return kaspi.set_setting("kaspi_fee_percent", float(args["percent"]))
        if name == "list_calculations":
            return db.client().table("calculations").select("title,inputs,result,created_at") \
                .eq("workspace_id", db.workspace_id(workspace)) \
                .order("created_at", desc=True).limit(args.get("limit", 10)).execute().data
        raise ValueError(f"unknown tool {name}")

    today = _almaty_today()
    system = SYSTEM.format(today=today, yesterday=today - timedelta(days=1))
    out = run_agent(system, TOOLS, dispatch, [{"role": "user", "content": task}])
    db.log_action(workspace, "data", "task", {"task": task}, {"answer": out})
    return out
