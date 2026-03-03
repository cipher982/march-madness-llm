# Handoff: March Madness LLM — 2026 Pre-Tournament Prep

**Date:** 2026-03-03
**Deadline:** Selection Sunday March 15, 2026 (12 days)
**Live URL:** marchmadness.drose.io (Coolify on clifford)

---

## Current State

| Area | Status |
|------|--------|
| Backend tests | ✅ 23 passing, 90% coverage |
| Backend hardening | ✅ race condition, rate limiting, sanitization, retries, health endpoint |
| Frontend TSX migration | ✅ all active files .tsx, WS error handling |
| Production Dockerfiles | ✅ nginx multi-stage, no dev servers |
| GitHub Actions CI | ✅ lint + pytest + tsc + build + Playwright |
| Playwright E2E + visual | ✅ 13 tests passing, baselines committed |
| Secrets → Infisical | ✅ migrated (see below) |
| **9 commits not pushed** | ❌ nothing has shipped to prod yet |
| Coolify not updated | ❌ still running old config, no Infisical |
| docker-compose.yml broken | ❌ references deleted .env file |
| Umami analytics | ❌ needs website ID |
| 2026 bracket data | ❌ blocked until March 15 |

---

## Key Discoveries

### Infisical Migration (done this session)
- Secrets moved from macOS Keychain + `.env` to **Infisical Cloud**
- Project: `march-madness-llm` (workspace ID: `6a99288c-3250-4c7f-8bf7-f58bbcbd64e9`)
- Org ID: `f87e812d-4955-4372-9d12-381f2eb7a5db`
- Two environments: `dev` (localhost config) and `prod` (marchmadness.drose.io config)
- CI service token stored in: macOS Keychain as `infisical-march-madness-ci` AND GitHub secret `INFISICAL_TOKEN`
- Token is read-only, never-expiring, covers dev + prod
- **Local dev:** `infisical run --env dev -- <command>` — no `.env`, no `.envrc`, no direnv needed
- **`.env` files deleted.** `docker-compose.yml` still references `env_file: .env` — this will break `docker compose up` locally until fixed

### Minio "credentials in git history" — FALSE ALARM
- Prior HANDOFF.md claimed hardcoded Minio creds were in git history — **verified this is wrong**
- `backend/scripts/` is in `.gitignore` and was never committed
- The creds are in `backend/scripts/upload_logos.py` on disk only (local file, never pushed)
- The Minio instance at `minio-nwcs0c4g0w8gcgow0gscgckg.5.161.97.53.sslip.io` IS live and the creds DO work — but this is a local-file-only situation, same as any `.env` file

### Playwright WS Mocking
- `page.routeWebSocket()` requires Playwright 1.48+; we have 1.58.2
- WS URL is `ws://localhost:8000/ws/simulate` (derived from `REACT_APP_BACKEND_URL`)
- Mock fires synchronously — simulation completes before intermediate state assertions run; scope assertions to `.simulating-box` container to avoid bracketry viz conflicts
- Visual regression baselines at `frontend/e2e/visual.spec.ts-snapshots/` (darwin/chromium)

### docker-compose.yml / Infisical gap
- `docker-compose.yml` has `env_file: .env` for both services — `.env` is now deleted
- Backend Dockerfile does NOT install Infisical CLI
- Fix needed before `docker compose up` works again

---

## Decisions Made

- **Infisical Cloud** (not self-hosted) for now. Lock-in risk acknowledged but acceptable for hobby project. Self-host on clifford is the escape hatch if needed.
- **No `.envrc` / direnv** — replaced entirely with `infisical run --` prefix. Not a partial migration.
- **Keep CRA** — don't migrate to Vite/Next.js with 12 days to tournament.
- **Playwright over Cypress** — first-class `routeWebSocket()` support.
- **No features for 2026** — polish and reliability only.

---

## Next Steps (priority order)

### 1. Fix docker-compose + Dockerfile for Infisical (blocking deploy)
In `docker-compose.yml`: remove `env_file: .env` from both services. Add `INFISICAL_TOKEN` as the only env var needed at runtime.

In `backend/Dockerfile`: install Infisical CLI and wrap the start command:
```dockerfile
RUN curl -1sLf 'https://artifacts.infisical.com/setup.deb.sh' | bash \
    && apt-get install -y infisical
CMD ["infisical", "run", "--env", "prod", "--", "uv", "run", "uvicorn", "mm_ai.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Push 9 commits to origin
```bash
git push origin main
```
(branch is ahead by 9 commits, nothing has shipped yet)

### 3. Update Coolify
- Add env var `INFISICAL_TOKEN` = value from `security find-generic-password -a "$USER" -s "infisical-march-madness-ci" -w`
- Update backend start command to use `infisical run --env prod --`
- Redeploy

### 4. Umami analytics
- Get website ID from `analytics.drose.io` for `marchmadness.drose.io`
- Add snippet to `frontend/public/index.html` before `</head>`

### 5. After March 15: bracket data
- Replace `backend/data/bracket_2024.json` with 2026 field
- Update `frontend/src/team_mappings.ts` for any new teams
- Verify logos exist for all 64 teams in `frontend/public/logos/optimized/50x50/`
- Full E2E test run with real data

---

## Reference

| Item | Location |
|------|----------|
| Backend source | `backend/mm_ai/` |
| Frontend source | `frontend/src/` |
| Infisical project | app.infisical.com → personal org → march-madness-llm |
| CI token (keychain) | `infisical-march-madness-ci` |
| CI token (GitHub) | repo secret `INFISICAL_TOKEN` |
| Playwright tests | `frontend/e2e/` |
| Visual baselines | `frontend/e2e/visual.spec.ts-snapshots/` |
| Run backend locally | `infisical run --env dev -- uv run uvicorn mm_ai.main:app --reload --port 8000` |
| Run frontend locally | `infisical run --env dev -- bun run start` |
| Run backend tests | `infisical run --env dev -- uv run pytest` |
| Regen visual baselines | `bunx playwright test --update-snapshots` (requires running dev server) |
| Uptime monitor | https://stats.uptimerobot.com/Jlo4zDIBm8 |
