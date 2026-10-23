---
name: jarvis-deploy
description: Ship a Jarvis backend change to production and verify it. Use after any backend commit, after Alisher adds an env variable in Vercel, or when Jarvis looks broken.
---

# Jarvis deploy

1. Commit and push to branch `claude/ai-agent-audio-multiagent-qb4qz5` (repo alisherisenov03/Ataria).
2. `mcp__Vercel__create_deployment` with teamId `team_GqKAboNJ4hAC2TOF0mc0T4BK`, skipAutoDetectionConfirmation 1, requestBody {name jarvis-backend, project prj_rRTQQWFnTpJ9fh2tZUIblILXTanc, target production, gitSource github alisherisenov03/Ataria ref branch}. Env changes need a new deployment (forceNew 1).
3. Wait for READY (`get_deployment`), then `curl https://jarvis-backend-alisher25.vercel.app/health`: every needed flag true.
4. Region must be icn1 (Supabase is ap-northeast-2, Seoul). Check `get_runtime_logs` for `chat ok in Xs` timings after Alisher's next conversation.
5. Broken: `get_runtime_logs` for errors, fix, redeploy. Never print env values.
