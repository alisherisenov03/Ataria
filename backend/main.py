import hmac
import os

import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config
import kaspi
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
    }
    return {"ok": True, "configured": configured}


@app.post("/chat")
def chat(body: ChatIn, authorization: str = Header(default=""), token: str = ""):
    _auth(authorization, token)
    return {"reply": orchestrator.chat(body.session_id, body.text)}


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
    return {"signed_url": r.json()["signed_url"]}


@app.post("/kaspi/sync")
def kaspi_sync(deep: bool = False, authorization: str = Header(default="")):
    """Called on a schedule by the database (pg_cron) or by hand."""
    _auth(authorization)
    return kaspi.sync(deep=deep)
