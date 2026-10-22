"""Meta webhooks: WhatsApp messages from Alisher go to Jarvis; replies go back to WhatsApp.

Only the owner's number gets automatic answers. Anyone else is stored in jarvis.messages
(status 'received') and left for Alisher to decide.
"""
import hashlib
import hmac

import httpx

import config
import db
import orchestrator


def verify_signature(body: bytes, header: str) -> bool:
    """Signed with the Meta app secret (WhatsApp) or the Instagram app secret (Instagram Login)."""
    for secret in (config.META_APP_SECRET, config.INSTAGRAM_APP_SECRET):
        if secret:
            expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
            if hmac.compare_digest(expected, header or ""):
                return True
    return False


def _digits(s: str) -> str:
    return "".join(ch for ch in s or "" if ch.isdigit())


def send_whatsapp_text(to: str, text: str) -> dict:
    r = httpx.post(
        f"https://graph.facebook.com/{config.META_GRAPH_VERSION}/{config.WHATSAPP_PHONE_NUMBER_ID}/messages",
        headers={"Authorization": f"Bearer {config.META_ACCESS_TOKEN}"},
        json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text[:4000]}},
        timeout=20,
    )
    if r.status_code >= 300:
        print(f"whatsapp send failed {r.status_code}: {r.text[:300]}")
    return {"status": r.status_code}


def _store(channel: str, sender: str, text: str, meta: dict):
    db.client().table("messages").insert({
        "workspace_id": db.workspace_id("ataria"), "channel": channel, "direction": "in",
        "body": text, "status": "received", "metadata": {"from": sender, **meta},
    }).execute()


def _handle_instagram(payload: dict) -> int:
    """Instagram DMs are stored for Alisher (no auto-replies to customers without his approval)."""
    n = 0
    for entry in payload.get("entry", []):
        # Live events arrive in entry[].messaging; dashboard "Test" events in entry[].changes[].value
        events = list(entry.get("messaging", []))
        events += [c.get("value") or {} for c in entry.get("changes", []) if c.get("field") == "messages"]
        for ev in events:
            msg = ev.get("message") or {}
            if not msg or msg.get("is_echo"):
                continue
            text = msg.get("text") or ("[вложение]" if msg.get("attachments") else "")
            _store("instagram", (ev.get("sender") or {}).get("id", ""), text, {"ig_mid": msg.get("mid")})
            n += 1
    return n


def handle(payload: dict) -> dict:
    if payload.get("object") == "instagram":
        return {"handled": _handle_instagram(payload)}
    handled = 0
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value") or {}
            for msg in value.get("messages", []):
                sender = _digits(msg.get("from", ""))
                if msg.get("type") == "text":
                    text = (msg.get("text") or {}).get("body", "")
                else:
                    text = f"[{msg.get('type')}]"  # voice notes and media: next step
                _store("whatsapp", sender, text, {"wa_id": msg.get("id"), "type": msg.get("type")})
                if config.OWNER_WHATSAPP and sender == _digits(config.OWNER_WHATSAPP):
                    if msg.get("type") == "text":
                        reply = orchestrator.chat(f"whatsapp:{sender}", text)
                    else:
                        reply = "Пока понимаю только текст. Голосовые сообщения скоро добавлю."
                    send_whatsapp_text(sender, reply)
                handled += 1
    return {"handled": handled}


def inbox(limit: int = 15) -> list[dict]:
    rows = (db.client().table("messages").select("channel,body,metadata,created_at")
            .eq("direction", "in").order("created_at", desc=True).limit(limit).execute().data)
    return [{"channel": r["channel"], "from": (r["metadata"] or {}).get("from"), "text": r["body"],
             "at": r["created_at"]} for r in rows]


def instagram_subscribe() -> dict:
    """Subscribe Alisher's Instagram business account to this app's webhooks (needed once per account)."""
    base = f"https://graph.instagram.com/{config.META_GRAPH_VERSION}"
    tok = {"access_token": config.INSTAGRAM_ACCESS_TOKEN}
    me = httpx.get(f"{base}/me", params={"fields": "user_id,username", **tok}, timeout=20)
    sub = httpx.post(f"{base}/me/subscribed_apps", params={"subscribed_fields": "messages", **tok}, timeout=20)
    return {"me_status": me.status_code, "me": me.json() if me.status_code == 200 else me.text[:300],
            "subscribe_status": sub.status_code, "subscribe": sub.text[:300]}
