"""Data & calculations agent: numbers, saved calculations."""
import ast
import operator as op

import db
from agents.runner import run_agent

SYSTEM = (
    "Ты агент «Данные и расчёты». Считаешь точно: любое вычисление делай через инструмент calculate, "
    "не в уме. Важные расчёты сохраняй через save_calculation. Отвечай коротко, по-русски, с итоговыми числами."
)

TOOLS = [
    {"name": "calculate", "description": "Вычислить арифметическое выражение (+ - * / ** % //, скобки).",
     "input_schema": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}},
    {"name": "save_calculation", "description": "Сохранить расчёт в базу.",
     "input_schema": {"type": "object", "properties": {
         "title": {"type": "string"}, "inputs": {"type": "object"}, "result": {"type": "object"}},
         "required": ["title", "result"]}},
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
        if name == "list_calculations":
            return db.client().table("calculations").select("title,inputs,result,created_at") \
                .eq("workspace_id", db.workspace_id(workspace)) \
                .order("created_at", desc=True).limit(args.get("limit", 10)).execute().data
        raise ValueError(f"unknown tool {name}")

    out = run_agent(SYSTEM, TOOLS, dispatch, [{"role": "user", "content": task}])
    db.log_action(workspace, "data", "task", {"task": task}, {"answer": out})
    return out
