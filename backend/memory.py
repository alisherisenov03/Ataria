import db

KINDS = ("preference", "lesson", "fact", "skill")


def remember(workspace: str, kind: str, content: str, shared: bool = False) -> dict:
    if kind not in KINDS:
        return {"error": f"kind must be one of {KINDS}"}
    row = db.client().table("memory").insert({
        "workspace_id": None if shared else db.workspace_id(workspace),
        "kind": kind,
        "content": content,
    }).execute().data[0]
    return {"saved": row["id"]}


def recall(workspace: str, query: str, limit: int = 8) -> list[dict]:
    """Shared memory plus this workspace's memory, newest first."""
    q = (
        db.client().table("memory")
        .select("kind,content,created_at")
        .or_(f"workspace_id.is.null,workspace_id.eq.{db.workspace_id(workspace)}")
        .order("created_at", desc=True)
        .limit(limit)
    )
    if query.strip():
        q = q.ilike("content", f"%{query.strip()}%")
    return q.execute().data
