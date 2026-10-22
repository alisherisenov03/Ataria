import hmac
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel

import config
import db
import kaspi
import meta
import orchestrator

app = FastAPI(title="Jarvis backend")
# The desktop app's window is served from http://127.0.0.1:<random port>; allow only that origin.
# Every call still needs the BACKEND_TOKEN, so this does not open anything up.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://127\.0\.0\.1:\d+$",
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


class ChatIn(BaseModel):
    text: str
    session_id: str = "default"


def _auth(authorization: str, token_q: str = ""):
    # Accepted if EITHER the Authorization header OR ?token= matches (some tools cannot set headers).
    header_token = authorization.removeprefix("Bearer ").strip()
    candidates = [t.strip() for t in (header_token, token_q) if t and t.strip()]
    if config.BACKEND_TOKEN and any(hmac.compare_digest(t, config.BACKEND_TOKEN) for t in candidates):
        return
    # Diagnostics only: lengths, never values.
    print(f"auth rejected: header_len={len(header_token)} query_len={len(token_q.strip())} "
          f"expected_len={len(config.BACKEND_TOKEN)}")
    raise HTTPException(status_code=401, detail="unauthorized")


@app.exception_handler(RequestValidationError)
async def _log_validation(request, exc):
    print("bad request body:", [(e.get("loc"), e.get("type")) for e in exc.errors()])
    return await request_validation_exception_handler(request, exc)


@app.get("/health")
def health():
    """Shows which settings are present (true/false only, never the values)."""
    configured = {
        "supabase": bool(config.SUPABASE_URL and config.SUPABASE_SERVICE_KEY),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "backend_token": bool(config.BACKEND_TOKEN),
        "elevenlabs": bool(config.ELEVENLABS_API_KEY),
        "elevenlabs_agent": bool(config.ELEVENLABS_AGENT_ID),
        "kaspi": bool(config.KASPI_TOKEN),
        "meta_verify_token": bool(config.META_VERIFY_TOKEN),
        "whatsapp": bool(config.META_ACCESS_TOKEN and config.WHATSAPP_PHONE_NUMBER_ID and config.META_APP_SECRET),
        "instagram_token": bool(config.INSTAGRAM_ACCESS_TOKEN),
        "instagram_app_secret": bool(config.INSTAGRAM_APP_SECRET),
    }
    return {"ok": True, "configured": configured}


@app.post("/chat")
def chat(body: ChatIn, authorization: str = Header(default=""), token: str = ""):
    _auth(authorization, token)
    started = time.monotonic()
    try:
        reply = orchestrator.chat(body.session_id, body.text)
        print(f"chat ok in {time.monotonic() - started:.1f}s")
        return {"reply": reply}
    except Exception as e:
        print(f"chat failed: {type(e).__name__}: {str(e)[:300]}")
        return {"reply": f"Не получилось обработать запрос: {type(e).__name__}. Подробности в логах бэкенда."}


@app.get("/voice/session")
def voice_session(authorization: str = Header(default="")):
    """Short-lived signed URL so the desktop app never holds the ElevenLabs key."""
    _auth(authorization)
    if not config.ELEVENLABS_API_KEY or not config.ELEVENLABS_AGENT_ID:
        raise HTTPException(status_code=503, detail="ElevenLabs is not configured")
    r = httpx.get(
        "https://api.elevenlabs.io/v1/convai/conversation/get-signed-url",
        params={"agent_id": config.ELEVENLABS_AGENT_ID},
        headers={"xi-api-key": config.ELEVENLABS_API_KEY},
        timeout=15,
    )
    if r.status_code != 200:
        print(f"elevenlabs get-signed-url {r.status_code}: {r.text[:300]}")
        raise HTTPException(status_code=502, detail=f"ElevenLabs {r.status_code}: {r.text[:200]}")
    return {"signed_url": r.json()["signed_url"], "briefing": _briefing()}


def _money(x) -> str:
    return f"{round(float(x)):,}".replace(",", " ")


def _unseen_dev_news() -> str:
    """Latest developer report the user has not heard yet (marked as heard once spoken)."""
    try:
        seen = int(kaspi._setting("dev_log_seen_id") or 0)
        rows = (db.client().table("dev_log").select("id,summary").gt("id", seen)
                .order("id", desc=True).limit(1).execute().data)
        if not rows:
            return ""
        kaspi.set_setting("dev_log_seen_id", rows[0]["id"])
        first = rows[0]["summary"].split(". ")[0].rstrip(".")
        return f"Новости от разработчика: {first[:220]}. "
    except Exception as e:
        print(f"dev news failed: {type(e).__name__}")
        return ""


def _briefing() -> str:
    """Opening line for a voice session: straight to the numbers instead of a generic greeting."""
    try:
        rows = kaspi.daily_sales(2)
        today = (datetime.now(timezone.utc) + timedelta(hours=5)).date().isoformat()
        by_day = {str(r["day"]): r for r in rows}
        yday = (datetime.now(timezone.utc) + timedelta(hours=5) - timedelta(days=1)).date().isoformat()
        parts = []
        if yday in by_day:
            parts.append(f"вчера {by_day[yday]['orders']} заказов на {_money(by_day[yday]['revenue'])} тенге")
        if today in by_day:
            parts.append(f"сегодня пока {by_day[today]['orders']} на {_money(by_day[today]['revenue'])}")
        return ("Слушаю, Алишер. " + (", ".join(parts).capitalize() + ". " if parts else "")
                + _unseen_dev_news() + "Что делаем?")
    except Exception as e:
        print(f"briefing failed: {type(e).__name__}")
        return "Слушаю, Алишер. Что делаем?"


@app.post("/kaspi/sync")
def kaspi_sync(deep: bool = False, quick: bool = False, authorization: str = Header(default="")):
    """Called on a schedule by the database (pg_cron) or by hand."""
    _auth(authorization)
    return kaspi.sync(deep=deep, quick=quick)


# Desktop app UI, served from here so UI changes ship without a new download.
# Rebuild with `npm run publish-ui` in desktop/.
APP_DIR = Path(__file__).parent / "static" / "app"
NO_CACHE = {"Cache-Control": "no-cache"}


@app.get("/app")
def app_redirect():
    return RedirectResponse("/app/")


@app.get("/app/")
def app_index():
    return FileResponse(APP_DIR / "index.html", media_type="text/html; charset=utf-8", headers=NO_CACHE)


@app.get("/app/renderer.js")
def app_script():
    return FileResponse(APP_DIR / "renderer.js", media_type="text/javascript; charset=utf-8", headers=NO_CACHE)


@app.get("/webhooks/meta")
def meta_verify(request: Request):
    """Meta calls this once when the webhook is set up."""
    q = request.query_params
    if (q.get("hub.mode") == "subscribe" and config.META_VERIFY_TOKEN
            and hmac.compare_digest(q.get("hub.verify_token", ""), config.META_VERIFY_TOKEN)):
        print("meta webhook verified")
        return PlainTextResponse(q.get("hub.challenge", ""))
    print(f"meta webhook verification failed: mode={q.get('hub.mode')} token_len={len(q.get('hub.verify_token', ''))}")
    raise HTTPException(status_code=403, detail="verification failed")


@app.post("/webhooks/meta")
async def meta_webhook(request: Request):
    body = await request.body()
    if not meta.verify_signature(body, request.headers.get("x-hub-signature-256", "")):
        print("meta webhook: bad or missing signature")
        raise HTTPException(status_code=401, detail="bad signature")
    try:
        payload = await request.json()
        print(f"meta webhook event: object={payload.get('object')}")
        return meta.handle(payload)
    except Exception as e:  # always 200 after a valid signature, or Meta keeps retrying
        print(f"meta webhook failed: {type(e).__name__}: {str(e)[:300]}")
        return {"handled": 0}
