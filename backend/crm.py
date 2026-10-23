"""Contacts (UGC creators, leads, suppliers) and outreach drafts. Nothing is ever sent from here."""
import db


def add_contact(workspace: str, name: str, platform: str = "", handle: str = "", phone: str = "",
                email: str = "", source: str = "", notes: str = "", metadata: dict | None = None) -> dict:
    row = {"workspace_id": db.workspace_id(workspace), "name": name, "platform": platform, "handle": handle.lstrip("@"),
           "phone": phone, "email": email, "source": source, "notes": notes, "metadata": metadata or {}}
    q = db.client().table("contacts")
    if row["handle"]:
        saved = q.upsert(row, on_conflict="workspace_id,platform,handle").execute().data
    else:
        saved = q.insert(row).execute().data
    return {"saved": {"name": name, "platform": platform, "handle": row["handle"], "id": saved[0]["id"]}}


def list_contacts(workspace: str, status: str | None = None, query: str | None = None, limit: int = 30) -> list[dict]:
    q = (db.client().table("contacts").select("id,name,platform,handle,phone,status,notes,source,metadata")
         .eq("workspace_id", db.workspace_id(workspace)).order("updated_at", desc=True).limit(min(limit, 100)))
    if status:
        q = q.eq("status", status)
    if query:
        q = q.or_(f"name.ilike.%{query}%,handle.ilike.%{query}%,notes.ilike.%{query}%")
    return q.execute().data


def _find(workspace: str, who: str) -> dict | None:
    rows = list_contacts(workspace, query=who.lstrip("@"), limit=5)
    exact = [r for r in rows if who.lstrip("@").lower() in (r["handle"].lower(), r["name"].lower())]
    hit = exact or rows
    return hit[0] if len(hit) == 1 or exact else None


def update_contact(workspace: str, who: str, status: str | None = None, notes: str | None = None) -> dict:
    c = _find(workspace, who)
    if not c:
        return {"error": f"не нашёл однозначно «{who}»"}
    patch = {k: v for k, v in (("status", status), ("notes", notes)) if v}
    db.client().table("contacts").update(patch).eq("id", c["id"]).execute()
    return {"updated": c["name"], **patch}


def draft_message(workspace: str, who: str, channel: str, body: str) -> dict:
    """Stores a draft only. Sending requires Alisher's explicit yes, then a separate step."""
    c = _find(workspace, who)
    if not c:
        return {"error": f"не нашёл однозначно «{who}»: сначала add_contact"}
    db.client().table("messages").insert({"workspace_id": db.workspace_id(workspace), "contact_id": c["id"],
                                          "channel": channel, "direction": "out", "body": body, "status": "draft"}).execute()
    return {"draft_saved_for": c["name"], "status": "draft", "note": "не отправлено, ждёт «да» Алишера"}


def list_drafts(workspace: str, limit: int = 20) -> list[dict]:
    rows = (db.client().table("messages").select("body,channel,created_at,contacts(name,handle)")
            .eq("workspace_id", db.workspace_id(workspace)).eq("direction", "out").eq("status", "draft")
            .order("created_at", desc=True).limit(limit).execute().data)
    return rows


def link_clicks(days: int = 7) -> dict:
    """Clicks on the WhatsApp tracking link, by source (reel, bio, ad)."""
    from datetime import datetime, timedelta, timezone
    since = (datetime.now(timezone.utc) - timedelta(days=max(1, min(int(days or 7), 90)))).isoformat()
    rows = db.client().table("link_clicks").select("src,created_at").gte("created_at", since).limit(5000).execute().data
    by = {}
    for r in rows:
        by[r["src"]] = by.get(r["src"], 0) + 1
    return {"days": days, "total": len(rows), "by_source": dict(sorted(by.items(), key=lambda x: -x[1]))}
