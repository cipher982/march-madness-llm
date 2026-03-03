# March Madness LLM - Agent Instructions

## Project Overview

NCAA March Madness bracket simulator using AI, seed-based logic, or random selection. Users pick a strategy, optionally provide preferences, and watch a real-time WebSocket-streamed bracket simulation with animated bracket visualization.

**Live URL:** `marchmadness.drose.io` (Coolify on clifford)
**Status:** Preparing for 2026 tournament (Selection Sunday: March 15, 2026)

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Backend** | FastAPI 0.115+ / Python 3.12 | Async, WebSocket streaming |
| **Frontend** | React 18 / TypeScript (partial) | CRA-based, `bracketry` for visualization |
| **LLM** | OpenAI gpt-4o-mini (63 calls/bracket) | Via `openai` SDK + LangSmith tracing |
| **Package Mgmt** | Backend: `uv` / Frontend: `bun` | Migrating frontend from npm to bun |
| **Containers** | Docker Compose (2 services) | Backend :8000, Frontend :3000 |
| **Deployment** | Coolify on clifford VPS | Domain: marchmadness.drose.io |
| **CI/CD** | GitHub Actions (to be built) | Currently: none (old workflow deleted) |
| **Linting** | Ruff (backend), ESLint (frontend) | Pre-commit hooks configured |

## Architecture

```
frontend/          React SPA
  ├── WebSocket ──→ backend/mm_ai/main.py (FastAPI)
  │                   ├── simulator.py (orchestrates tournament)
  │                   ├── deciders.py (AI/seed/random decision functions)
  │                   └── bracket.py (data structures: Team/Matchup/Round/Region/Bracket)
  └── HTTP GET ───→ /api/bracket_start (initial bracket data)

data/
  ├── bracket_2024.json  → Initial 64-team seedings (NEEDS 2026 UPDATE)
  └── current_state.json → Partial tournament state (stale)
```

## Key Files

| File | Purpose | Status |
|------|---------|--------|
| `backend/mm_ai/main.py` | FastAPI app, routes, WebSocket endpoint | Needs error handling, config cleanup |
| `backend/mm_ai/bracket.py` | Tournament data structures (Team/Matchup/Round/Region/Bracket) | Needs type hints, Pydantic validation |
| `backend/mm_ai/simulator.py` | Tournament simulation orchestration | Has race condition in concurrent updates |
| `backend/mm_ai/deciders.py` | AI/seed/random decision functions | Hardcoded model, no retry logic |
| `frontend/src/App.js` | Main React component | Should be .tsx, missing WS error handling |
| `frontend/src/components/BracketryTest.tsx` | Bracket visualization (bracketry lib) | Active component, decent quality |
| `frontend/src/components/BracketDisplay.js` | OLD bracket display | DEAD CODE - remove |
| `frontend/src/team_mappings.ts` | Team name → logo ID mappings (1440 lines) | Has encoding bug (San Jos√© State) |

## Known Issues (Priority Order)

### P0 - Security
- `backend/scripts/upload_logos.py` has **hardcoded Minio credentials** in git history. Rotate immediately.
- `deciders.py` has unsanitized `user_preferences` in LLM prompt (injection vector)
- `main.py` leaks exception details to client responses

### P1 - Reliability
- **Zero tests** - `tests/` directory is empty despite pytest configured
- No WebSocket error handler on frontend (connection failures invisible to user)
- No OpenAI API retry/backoff logic
- Race condition in `simulator.py` concurrent bracket state updates
- No rate limiting on simulation endpoint

### P2 - Code Quality
- Backend has **zero type hints** across all files
- Frontend mixes .js and .tsx (5 JS files, 2 TSX files)
- Dead code: `BracketDisplay.js`, commented-out lines in `App.js`
- Duplicated `ROUND_NAMES` constant in bracket.py and simulator.py
- Console.log debug statements in `index.js`

### P3 - Infrastructure
- No CI/CD pipeline (old GitHub Actions workflow was deleted)
- Dockerfiles run dev servers in production (`--reload`, `npm start`)
- No `/health` endpoint defined (health check in docker-compose will fail)
- No analytics (Umami not integrated)
- Bracket data frozen at 2024

## Development

### Local Setup
```bash
# Backend
cd backend && uv sync
# Frontend
cd frontend && bun install
# Both via Docker
docker compose up
```

### Environment Variables
```
OPENAI_API_KEY      # From macOS Keychain via .envrc
LANGSMITH_API_KEY   # From macOS Keychain via .envrc
LANGSMITH_TRACING   # true
BACKEND_URL         # http://localhost:8000
FRONTEND_PORT       # 3001
```

### Testing Strategy (TO BE BUILT)

**Backend (pytest):**
- Unit: bracket logic, decider functions, data loading
- Integration: WebSocket endpoint with mocked OpenAI
- Use `TestClient.websocket_connect()` for WS tests
- Mock OpenAI via FastAPI dependency injection

**Frontend (Playwright):**
- E2E: full simulation flow with mocked WS
- Visual regression: `toHaveScreenshot()` at stable milestones
- Use `page.routeWebSocket()` for deterministic WS testing

**CI (GitHub Actions):**
- Backend: ruff lint + pytest + coverage
- Frontend: TypeScript check + bun test + Playwright E2E
- Visual: Playwright screenshot baselines in repo

## Conventions

- **Commits:** Atomic, descriptive. Never amend, never skip hooks.
- **Python:** Ruff format, line-length 120, double quotes. Type hints required on new code.
- **TypeScript:** All new/modified components must be `.tsx` with proper types. No `any`.
- **Secrets:** Never in code. Use env vars loaded from Keychain (`.envrc`).
- **LLM calls:** Use z.ai (GLM-5) for dev/personal. OpenAI for production bracket generation.

## Deployment

Deployed via Coolify on clifford VPS. See `~/git/me/mytech/AGENTS.md` for Coolify operations.

Domain: `marchmadness.drose.io`
Uptime: https://stats.uptimerobot.com/Jlo4zDIBm8
