import hmac

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

import config
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
    return {"ok": True}


@app.post("/chat")
def chat(body: ChatIn, authorization: str = Header(default="")):
    _auth(authorization)
    return {"reply": orchestrator.chat(body.session_id, body.text)}
