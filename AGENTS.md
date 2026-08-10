# March Madness LLM - Agent Instructions

NCAA March Madness bracket simulator using AI, seed-based logic, or random selection. Users pick a strategy, optionally give preferences, and watch a real-time WebSocket-streamed bracket simulation.

**Live URL:** `marchmadness.drose.io` (API: `api.marchmadness.drose.io`)

## Tech Stack

| Layer | Stack |
|-------|-------|
| **Backend** | FastAPI / Python 3.12, async + WebSocket (`uv`) |
| **Frontend** | React 18 / TS (partial), CRA + `bracketry`, `bun` |
| **LLM** | OpenAI `gpt-4o-mini` via OpenAI SDK + LangSmith tracing |
| **Containers** | Docker Compose (backend :8000, frontend :3000) |
| **Deploy** | manual-app `marchmadness` on clifford (migrated off Coolify) |

## Architecture

```
frontend/  WSS ──► backend/mm_ai/main.py (FastAPI)
  ├── simulator.py   tournament orchestration
  ├── deciders.py    AI / seed / random decision functions
  └── bracket.py     Team/Matchup/Round/Region data structures

data/bracket_2024.json  initial 64-team seedings; data/current_state.json  stale
```

## Setup / Env

```bash
cd backend && uv sync      # backend
cd frontend && bun install # frontend
docker compose up          # both
```

Env vars (Infisical project `march-madness-llm`): `OPENAI_API_KEY`, `LANGSMITH_API_KEY` (+ `LANGSMITH_TRACING=true`), `BACKEND_URL=http://localhost:8000`, `FRONTEND_PORT=3001`.

## Conventions

- Commits: atomic, descriptive; never amend or skip hooks.
- Python: Ruff format, line-length 120, double quotes, type hints required on new code.
- TypeScript: new/modified components `.tsx` with proper types; no `any`.
- Secrets: never in code. Use `infisical run --env dev -- <command>`. No `.env` files.

## Known Issues

- `backend/scripts/upload_logos.py` has hardcoded Minio credentials in git history (rotate).
- `deciders.py` uses unsanitized `user_preferences` in the prompt (injection); `main.py` leaks exception details to clients.
- `backend/mm_ai/simulator.py` has a race condition in concurrent bracket-state updates.
- Dead code: `frontend/src/components/BracketDisplay.js`; commented-out lines in `App.js`.
- No `/health` endpoint; Docker runs dev servers in prod (`--reload`, `npm start`); Umami not integrated; bracket data frozen at 2024.