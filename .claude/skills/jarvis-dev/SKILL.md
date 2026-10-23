---
name: jarvis-dev
description: How Jarvis is built and how to change it safely: files, agents, tools, memory, voice chain. Use before editing anything in backend/ or desktop/, or when Alisher asks Jarvis to learn something new.
---

# Jarvis development

Voice chain: desktop app (right Ctrl) → ElevenLabs agent `agent_8601m5h2kcraff2vwmfqybq9ck1y` → webhook `ask_jarvis` → `POST /chat` (FastAPI on Vercel) → `orchestrator.chat` (claude-haiku-5-5, fallback sonnet) → tools → reply spoken by ElevenLabs. First line = `/voice/session` briefing (first session of the day only).

Files: `backend/orchestrator.py` (system prompt split: static SYSTEM cached + DYNAMIC per request; TOOLS; dispatch), `agents/runner.py` (tool loop, prompt caching, parallel tools, web_search fallback), `agents/data.py`, `agents/research.py`, `agents/vision.py`, `kaspi.py`, `kaspi_market.py`, `crm.py`, `instagram.py` (Windsor), `memory.py`, `meta.py`.

Adding an ability: tool schema in TOOLS + branch in dispatch + one rule line in SYSTEM. Keep answers short (voice). Reads must be fast: no sequential DB calls, parallelise.

Safety: secrets only in Vercel env; irreversible actions (sending messages, posting, payments, Kaspi replies) only after Alisher's "да"; drafts by default.
Checks before deploy: `python3 -m pytest -q` in backend, `python3 -c "import main"`.
