import hmac
import os

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

import config
import kaspi
import orchestrator

app = FastAPI(title="Jarvis backend")


class ChatIn(BaseModel):
    text: str
    session_id: str = "default"


def _auth(authorization: str):
    token = authorization.removeprefix("Bearer ").strip()
    if not config.BACKEND_TOKEN or not hmac.compare_digest(token, config.BACKEND_TOKEN):
        raise HTTPException(status_code=401, detail="unauthorized")


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
def chat(body: ChatIn, authorization: str = Header(default="")):
    _auth(authorization)
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
