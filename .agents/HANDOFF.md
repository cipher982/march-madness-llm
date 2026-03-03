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
| Production Dockerfiles | ✅ nginx multi-stage, Infisical CLI installed via direct binary |
| GitHub Actions CI | ✅ lint + pytest + tsc + build + Playwright |
| Playwright E2E + visual | ✅ 13 tests passing, baselines committed |
| Secrets → Infisical | ✅ migrated and working in prod |
| docker-compose.yml | ✅ no more env_file: .env, passes INFISICAL_TOKEN |
| Umami analytics | ✅ snippet live on marchmadness.drose.io |
| Coolify deployed | ✅ both containers healthy, commit a1adf9a |
| 2026 bracket data | ❌ blocked until March 15 |

---

## Key Discoveries

### Infisical Migration (done session 2)
- Secrets moved from macOS Keychain + `.env` to **Infisical Cloud**
- Project: `march-madness-llm` (workspace ID: `6a99288c-3250-4c7f-8bf7-f58bbcbd64e9`)
- Two environments: `dev` (localhost config) and `prod` (marchmadness.drose.io config)
- CI service token stored in: macOS Keychain as `infisical-march-madness-ci` AND GitHub secret `INFISICAL_TOKEN`
- **Local dev:** `infisical run --env dev -- <command>` — no `.env`, no `.envrc`, no direnv needed

### Infisical CLI in Docker (session 3)
- The APT setup.deb.sh fails on Debian 13 (trixie) — package not found
- The CLI lives in a **separate GitHub repo**: `https://github.com/Infisical/cli`
- Binary URL format: `https://github.com/Infisical/cli/releases/download/v{VERSION}/cli_{VERSION}_linux_amd64.tar.gz`
- Currently pinned to v0.43.58 in backend/Dockerfile
- **To upgrade**: update the version in backend/Dockerfile

### Umami Analytics (session 3)
- Umami is deployed on clifford at container `umami-es84cow0os8kc80wgkg0g408`
- URL: `analytics.drose.io` (Caddy label-based routing)
- A stale Caddy route for `analytics.drose.io → 172.18.0.1:3000` (Grafana's host port) was overriding Umami
- Fixed by deleting route index 13 via Caddy Admin API: `DELETE http://localhost:2019/config/apps/http/servers/srv0/routes/13`
- **NOTE**: This Caddy fix is in-memory only — if Coolify regenerates the proxy config, the stale route may return
  - Root cause: some historical Coolify app had analytics.drose.io as FQDN and was deleted; the route persisted in autosave.json
  - If it breaks again: SSH to clifford → `docker exec coolify-proxy curl -s DELETE http://localhost:2019/config/apps/http/servers/srv0/routes/INDEX`
  - Find the index: check which route has `upstreams.dial = 172.18.0.1:3000` for host analytics.drose.io
- **Website ID**: `680a2d09-14dd-45d7-8b03-32cbcf459d12` (created directly in Umami DB)
- **Access Umami admin**: `analytics.drose.io` (login: admin, password: unknown — check Coolify Umami service for APP_SECRET/DB creds; password bcrypt is `$2a$10$KQFL...`)

### Coolify App Config (r0w0c0s)
- App UUID: `r0w0c0s`
- Env vars currently set:
  - `BACKEND_URL`: https://api.marchmadness.drose.io (build-time, used as REACT_APP_BACKEND_URL)
  - `BACKEND_PORT`: 50000 (host port mapping)
  - `FRONTEND_PORT`: empty (uses default 3000)
  - `INFISICAL_TOKEN`: set (runtime, fetches prod secrets from Infisical)
- Removed stale `OPENAI_API_KEY` from Coolify (now in Infisical prod)

### Minio "credentials in git history" — FALSE ALARM
- Prior HANDOFF.md claimed hardcoded Minio creds were in git history — **verified this is wrong**
- `backend/scripts/` is in `.gitignore` and was never committed

### Playwright WS Mocking
- `page.routeWebSocket()` requires Playwright 1.48+; we have 1.58.2
- WS URL is `ws://localhost:8000/ws/simulate` (derived from `REACT_APP_BACKEND_URL`)
- Visual regression baselines at `frontend/e2e/visual.spec.ts-snapshots/` (darwin/chromium)

---

## Decisions Made

- **Infisical Cloud** (not self-hosted) for now.
- **No `.envrc` / direnv** — replaced entirely with `infisical run --` prefix.
- **Keep CRA** — don't migrate to Vite/Next.js with 12 days to tournament.
- **Playwright over Cypress** — first-class `routeWebSocket()` support.
- **No features for 2026** — polish and reliability only.
- **Skip 2026 bracket update** — stick with 2024 data until after Selection Sunday (March 15).

---

## Next Steps (priority order)

### 1. After March 15: bracket data
- Replace `backend/data/bracket_2024.json` with 2026 field
- Update `frontend/src/team_mappings.ts` for any new teams
- Verify logos exist for all 64 teams in `frontend/public/logos/optimized/50x50/`
- Full E2E test run with real data

### 2. Monitor Caddy routing for analytics.drose.io
- If Grafana starts showing at analytics.drose.io again, re-run the Caddy API delete fix
- Long-term: find the stale route's origin in Coolify and remove it cleanly

### 3. Umami admin password
- Unknown. Can reset via: update bcrypt hash in Umami postgres DB
  - DB: `docker exec postgresql-es84cow0os8kc80wgkg0g408 sh -c "PGPASSWORD=A9SKCxZUstzVQOgJTlRy05wyzQaUuyQx psql -U 4rfR7GJFefbxMc8j -d umami"`
  - Reset: `UPDATE "user" SET password = '<new-bcrypt-hash>' WHERE username = 'admin';`

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
| Umami website ID | `680a2d09-14dd-45d7-8b03-32cbcf459d12` |
| Infisical CLI repo | https://github.com/Infisical/cli |
