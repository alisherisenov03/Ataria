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
    if not config.META_APP_SECRET:
        return False
    expected = "sha256=" + hmac.new(config.META_APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header or "")


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


def handle(payload: dict) -> dict:
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
