import json
from typing import Callable

import anthropic

import config

_client = None


def _api():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _create(model: str, **kw):
    try:
        try:
            return _api().messages.create(model=model, **kw)
        except (anthropic.NotFoundError, anthropic.PermissionDeniedError):
            if model == config.ANTHROPIC_MODEL:
                raise
            return _api().messages.create(model=config.ANTHROPIC_MODEL, **kw)
    except anthropic.APIStatusError as e:
        print(f"anthropic error {e.status_code}: {str(e.message)[:300]}")
        raise


def run_agent(system: str, tools: list[dict], dispatch: Callable[[str, dict], object],
              messages: list[dict], max_steps: int = 8, model: str | None = None,
              max_tokens: int = 1500) -> str:
    """Tool-use loop shared by the orchestrator and every sub-agent."""
    messages = list(messages)
    for _ in range(max_steps):
        resp = _create(model or config.ANTHROPIC_MODEL, max_tokens=max_tokens,
                       system=system, tools=tools, messages=messages)
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text").strip()
        results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            try:
                out = dispatch(block.name, block.input)
            except Exception as e:  # report to the model instead of crashing the call
                out = {"error": str(e)}
            results.append({
                "type": "tool_result", "tool_use_id": block.id,
                "content": json.dumps(out, ensure_ascii=False, default=str),
            })
        messages.append({"role": "user", "content": results})
    return "Не смог закончить задачу за отведённое число шагов."
