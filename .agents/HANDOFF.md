# Handoff: March Madness LLM — 2026 Tournament Prep

**Date:** 2026-03-02
**Session:** Research, codebase audit, project planning
**Next session:** Begin implementation (testing harness first, then systematic cleanup)

## Situation

NCAA March Madness bracket simulator needs to be production-ready by **Selection Sunday, March 15, 2026** (13 days). The app works but is rough — zero tests, zero type hints, security issues, dead code, dev servers in Docker production builds. Goal is **polish and hardening, not new features**. The agent team must be fully self-sufficient for QA — no human QA available.

## Current State

| Area | Status | Details |
|------|--------|---------|
| **Backend** | Functional, fragile | FastAPI + WebSocket works. Zero tests, zero type hints, hardcoded config everywhere |
| **Frontend** | Functional, messy | React 18, mixed JS/TSX (5 JS files, 2 TSX). No WS error handling. Dead code. |
| **Bracket Data** | Stale (2024) | `backend/data/bracket_2024.json` — needs 2026 update after March 15 |
| **CI/CD** | None | Old GitHub Actions workflow was deleted. No pipeline exists. |
| **Docker** | Dev-only | Both containers run dev servers (`--reload`, `npm start`). No production builds. |
| **Tests** | Zero | `tests/__init__.py` exists but empty. pytest configured in pyproject.toml but no tests. |
| **Deployment** | Live | `marchmadness.drose.io` via Coolify on clifford. Uptime monitoring active. |
| **LLM** | Works | 63 gpt-4o-mini calls per bracket, ~$0.002/bracket. LangSmith tracing enabled. |

## Key Discoveries

### Security (Fix First)
1. **`backend/scripts/upload_logos.py` lines 28-32** — Hardcoded Minio credentials (access_key + secret_key) committed to git. **Must rotate these credentials.** Even if file is deleted, they're in git history.
2. **`backend/mm_ai/deciders.py` line 88** — `user_preferences` is interpolated directly into LLM prompt via `.format()`. Prompt injection vector. User can override system instructions.
3. **`backend/mm_ai/main.py` line 40** — `str(exc)` sent to client in error responses. Leaks internal details.

### Backend Code Issues (by file)

**`main.py` (138 lines):**
- Line 25-26: `assert frontend_port is not None` — crashes with bad error in prod. Use proper env var handling.
- Line 70: CORS origins hardcoded (`marchmadness.drose.io`). Should be env var.
- Lines 108-138: WebSocket endpoint has no try/except around `receive_json()`. Malformed JSON crashes connection.
- No `/health` endpoint defined despite docker-compose health check expecting one.

**`bracket.py` (330 lines):**
- Zero type hints on any class or method.
- Lines 112-135: JSON loading assumes keys exist, no validation. Single typo in data file crashes app.
- Lines 154-155: Matchup ID calculation uses magic string manipulation (`region_name[0].upper()` + `matchup_id[1:]`).
- `round_progression` list duplicated here AND in simulator.py.
- Lines 156-168: Can silently set winner to `None` if AI returns slightly different team name.

**`simulator.py` (203 lines):**
- **Race condition** lines 97-119: Multiple coroutines modify `self.bracket` concurrently via `process_match`. No asyncio.Lock.
- Line 95: `Semaphore(5)` but comment says "Allow 3 concurrent requests". Hardcoded, should be configurable.
- Line 38: UUID truncated to 8 chars — collision risk.
- No error handling if decision function raises mid-round — WebSocket not notified, round results incomplete.

**`deciders.py` (110 lines):**
- Line 10: `MODEL = "gpt-4o-mini"` hardcoded. Should be env var.
- Line 39: `client=None` default parameter but immediately raises if None. Should be required.
- Line 100: `json.loads()` on OpenAI response with no try/except.
- Line 101: Winner matching is exact string equality — if AI returns "University of Connecticut" and bracket says "UConn", wrong team selected. Should match by seed or fuzzy.
- Lines 105, 108: Uses `print()` instead of `logging`.

### Frontend Code Issues

**`App.js` (187 lines) — should be App.tsx:**
- Lines 76-108: WebSocket has `onopen`, `onmessage`, `onclose` but **no `onerror` handler**. Connection failures invisible to user.
- No reconnection logic. No timeout. If backend is down, user sees "Simulating..." forever.
- Line 42: Commented-out API key state (dead code).
- Line 178: Commented-out BracketDisplay component (dead code).

**`BracketDisplay.js` (98 lines):** DEAD CODE. Replaced by BracketryTest.tsx. Delete it.

**`BracketryTest.tsx` (215 lines):**
- Line 23: `bracket: any` — lazy typing.
- Line 51: Key regenerated with `Math.random()` on every bracket change — could cause unnecessary re-renders.
- Hardcoded 700px height — not responsive.

**`SimulateButton.js`:** `onError` prop defined but never called.
**`SimulationStatus.js`:** No null-check on `region` before `.charAt()`.
**`team_mappings.ts` line 1040:** Encoding bug: `"San Jos√© State"` (mojibake).
**`index.js` line 7:** `console.log('index.js file loaded')` — debug noise.
**`api.js`:** No axios timeout configured (defaults to 0 = infinite).

### Infrastructure
- `backend/Dockerfile`: Runs `uvicorn --reload` (dev mode). No HEALTHCHECK instruction. No EXPOSE.
- `frontend/Dockerfile`: Runs `npm start` (CRA dev server). Installs npm globally (unnecessary). No production build stage.
- `.github/` directory exists but is empty — old workflow was deleted in commit `21ab98d`.
- `.envrc` correctly loads secrets from macOS Keychain — good pattern for local dev.
- No `.dockerignore` found.

## Decisions Made & Why

1. **Playwright over Cypress for E2E** — Playwright has first-class WebSocket mocking via `page.routeWebSocket()` (added v1.48). Cypress can't intercept/mock WS frames natively. Critical for testing streaming UI deterministically.

2. **Keep CRA, don't migrate to Vite/Next.js** — Too risky with 13 days to tournament. Convert JS→TSX incrementally within existing CRA setup.

3. **Polish and harden, no new features** — The app's value is the real-time animated experience, not prediction accuracy. Focus on reliability, testing, and professional polish.

4. **Testing as primary deliverable** — Agent team must be self-sufficient for QA. Testing infrastructure (unit + integration + E2E + visual) is the foundation everything else builds on.

5. **Use z.ai (GLM-5) for dev, keep OpenAI for prod** — Flat-rate z.ai avoids dev cost. Production stays on gpt-4o-mini for quality.

6. **Frontend stays on bun** (migrate from npm) per user's standard toolchain.

## How to Work on This

### Testing Stack to Build
- **Backend unit tests:** `pytest` + `pytest-asyncio`. Test bracket logic, decider functions (mocked), data loading/validation. Use `TestClient.websocket_connect()` for WS integration tests.
- **Mock OpenAI:** Use FastAPI `app.dependency_overrides` to inject fake OpenAI client. Never call real API in tests.
- **Frontend E2E:** Playwright. Use `page.routeWebSocket()` to feed deterministic match sequences. Assert on DOM state, not timing.
- **Visual regression:** Playwright `toHaveScreenshot()` at stable milestones (empty bracket, mid-simulation, completed bracket). Baselines in git. Run in Docker for consistency.
- **CI:** GitHub Actions. Backend (ruff + pytest + coverage) and frontend (tsc + playwright) as separate jobs.

### Key Principles
- Read `AGENTS.md` in repo root — it has the full status and conventions.
- Read `VISION.md` for scope decisions (what's in/out for 2026).
- **Never amend commits. Never skip hooks.**
- **No `any` types in TypeScript.** All new code must be properly typed.
- **Python type hints required** on all new/modified functions.
- Secrets from Keychain via `.envrc` — never hardcode, never create `.env` files.

### Common Gotchas
- `pyproject.toml` has `addopts = "-v --cov"` which will fail until tests exist. Either add tests first or remove `--cov` temporarily.
- Frontend `BracketryTest.tsx` is the ACTIVE bracket component. `BracketDisplay.js` is dead.
- The bracket JSON format has two schemas: `bracket_2024.json` (initial seedings) and `current_state.json` (partial results). They're incompatible structures.
- Simulator creates a new `AsyncOpenAI` client per simulation instance — should be shared/pooled.

## Next Steps (Priority Order)

### Phase 1: Testing Foundation
1. Add `pytest-asyncio`, `httpx`, `asgi-lifespan` to backend dev deps
2. Create `backend/tests/conftest.py` with fixtures (TestClient, mocked OpenAI, sample bracket data)
3. Write unit tests for `bracket.py` — bracket loading, matchup progression, winner updates, edge cases
4. Write unit tests for `deciders.py` — seed decider, random decider, AI decider with mocked client
5. Write integration test for WebSocket simulation flow with mocked decider
6. Set up Playwright in frontend — `bun add -D @playwright/test`
7. Write E2E test: load page → select seed decider → simulate → verify bracket completes
8. Add visual regression baseline screenshots

### Phase 2: Code Hardening
9. Add type hints to ALL backend Python files
10. Convert all frontend .js components to .tsx with proper types
11. Fix WebSocket error handling (frontend `onerror`, reconnection, timeout)
12. Add OpenAI retry logic with exponential backoff
13. Fix race condition in simulator (add asyncio.Lock for bracket state updates)
14. Add proper `/health` endpoint
15. Sanitize user_preferences before prompt interpolation
16. Remove dead code (BracketDisplay.js, commented lines, console.logs)
17. Deduplicate ROUND_NAMES constant
18. Fix team name matching in deciders (case-insensitive or seed-based)

### Phase 3: Infrastructure
19. Create production Dockerfiles (multi-stage builds, no dev servers)
20. Create GitHub Actions CI workflow (lint + test + build)
21. Add Umami analytics snippet
22. Migrate frontend from npm to bun
23. Create `.dockerignore` files
24. Add rate limiting to simulation endpoint

### Phase 4: Tournament Prep (after March 15)
25. Update bracket data with 2026 tournament field
26. Update team_mappings.ts for any new teams
27. Verify all team logos exist
28. Full E2E test with 2026 data
29. Deploy and monitor

## Reference

| Item | Location |
|------|----------|
| Backend source | `backend/mm_ai/` (main.py, bracket.py, simulator.py, deciders.py) |
| Frontend source | `frontend/src/` (App.js, components/) |
| Bracket data | `backend/data/bracket_2024.json` |
| Docker setup | `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` |
| Project docs | `AGENTS.md`, `VISION.md` (both in repo root) |
| Local secrets | `.envrc` (loads from macOS Keychain) |
| Pre-commit | `backend/.pre-commit-config.yaml` (ruff) |
| Logo assets | `frontend/public/logos/` (400+ PNGs), optimized at `logos/optimized/50x50/*.webp` |
| Team mappings | `frontend/src/team_mappings.ts` (1440 lines, has encoding bug line ~1040) |
| Coolify/deploy | `~/git/me/mytech/AGENTS.md` for server ops |
| Uptime monitor | https://stats.uptimerobot.com/Jlo4zDIBm8 |
