from functools import lru_cache

from supabase import ClientOptions, create_client

import config


@lru_cache(maxsize=1)
def client():
    # Everything the agents own lives in the `jarvis` schema, never in `public`.
    return create_client(
        config.SUPABASE_URL,
        config.SUPABASE_SERVICE_KEY,
        options=ClientOptions(schema="jarvis"),
    )


@lru_cache(maxsize=16)
def workspace_id(slug: str) -> str:
    rows = client().table("workspaces").select("id").eq("slug", slug).execute().data
    if not rows:
        raise ValueError(f"unknown workspace: {slug}")
    return rows[0]["id"]


def workspace_slugs() -> list[str]:
    return [r["slug"] for r in client().table("workspaces").select("slug").execute().data]


def log_action(workspace: str | None, agent: str, action: str, input=None, output=None, success=True):
    client().table("agent_logs").insert({
        "workspace_id": workspace_id(workspace) if workspace else None,
        "agent": agent,
        "action": action,
        "input": input,
        "output": output,
        "success": success,
    }).execute()
