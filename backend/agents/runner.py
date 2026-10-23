import json
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

import anthropic

import config

_client = None


def _api():
    global _client
    if _client is None:
        # Keys not scoped to a workspace need the workspace id on every request.
        headers = {"anthropic-workspace-id": config.ANTHROPIC_WORKSPACE_ID} if config.ANTHROPIC_WORKSPACE_ID else None
        _client = anthropic.Anthropic(default_headers=headers)
    return _client


def _is_web_search(t: dict) -> bool:
    return str(t.get("type", "")).startswith("web_search")


def _create(model: str, **kw):
    def call(m, k):
        return _api().messages.create(model=m, **k)

    try:
        try:
            return call(model, kw)
        except (anthropic.NotFoundError, anthropic.PermissionDeniedError):
            if model == config.ANTHROPIC_MODEL:
                raise
            return call(config.ANTHROPIC_MODEL, kw)
        except anthropic.BadRequestError as e:
            # the fast model may not support the web search server tool: retry once without it
            tools = kw.get("tools") or []
            if any(_is_web_search(t) for t in tools):
                print(f"anthropic 400 with web_search, retrying without it: {str(e.message)[:200]}")
                kw2 = {**kw, "tools": [t for t in tools if not _is_web_search(t)]}
                return call(model, kw2)
            raise
    except anthropic.APIStatusError as e:
        print(f"anthropic error {e.status_code}: {str(e.message)[:300]}")
        raise


def _cached(system, tools):
    """Mark the static prefix (system blocks, tool list) as cacheable so repeat turns are faster and cheaper."""
    if isinstance(system, list):
        system = [dict(b) for b in system]
        system[0]["cache_control"] = {"type": "ephemeral"}
    if tools:
        tools = [dict(t) for t in tools]
        tools[-1]["cache_control"] = {"type": "ephemeral"}
    return system, tools


def run_agent(system: str, tools: list[dict], dispatch: Callable[[str, dict], object],
              messages: list[dict], max_steps: int = 8, model: str | None = None,
              max_tokens: int = 1500) -> str:
    """Tool-use loop shared by the orchestrator and every sub-agent."""
    messages = list(messages)
    for _ in range(max_steps):
        sys_, tools_ = _cached(system, tools)
        resp = _create(model or config.ANTHROPIC_MODEL, max_tokens=max_tokens,
                       system=sys_, tools=tools_, messages=messages)
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason == "pause_turn":  # long server-tool turn (web search): let it continue
            continue
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text").strip()
        calls = [b for b in resp.content if b.type == "tool_use"]

        def run(block):
            try:
                out = dispatch(block.name, block.input)
            except Exception as e:  # report to the model instead of crashing the call
                out = {"error": str(e)}
            return {"type": "tool_result", "tool_use_id": block.id,
                    "content": json.dumps(out, ensure_ascii=False, default=str)}

        if len(calls) > 1:  # independent tool calls run side by side
            with ThreadPoolExecutor(max_workers=len(calls)) as pool:
                results = list(pool.map(run, calls))
        else:
            results = [run(b) for b in calls]
        messages.append({"role": "user", "content": results})
    return "Не смог закончить задачу за отведённое число шагов."
