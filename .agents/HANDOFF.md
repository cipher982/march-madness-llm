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
| Production Dockerfiles | ✅ nginx multi-stage, entrypoint.sh for self-hosted Infisical |
| GitHub Actions CI | ✅ lint + pytest + tsc + build + Playwright |
| Playwright E2E + visual | ✅ 13 tests passing, baselines committed |
| Secrets → Infisical (self-hosted) | ✅ migrated from cloud to secrets.drose.io |
| docker-compose.yml | ✅ no env_file, passes INFISICAL_CLIENT_ID/SECRET |
| Umami analytics | ✅ snippet live on marchmadness.drose.io |
| Coolify deployed | ✅ both containers healthy |
| 2026 bracket data | ❌ blocked until March 15 |

---

## Key Discoveries

### Self-Hosted Infisical (session 4)
- Deployed at **secrets.drose.io** on clifford
- Coolify service UUID: `ncs84sgckcs08c4wsc0ogwwo`
- Image: `infisical/infisical:v0.158.6` (NOT `-postgres` suffix — that tag doesn't exist anymore)
- Admin account: `david@drose.io` (password in macOS Keychain: `infisical-admin-march-madness`)
- **CRITICAL KEYS** (losing these = losing all encrypted secrets):
  - `ENCRYPTION_KEY=REDACTED_ENCRYPTION_KEY`
  - `AUTH_SECRET=REDACTED_AUTH_SECRET`
- Postgres/Redis passwords in Coolify DB for service `ncs84sgckcs08c4wsc0ogwwo`

### Infisical Project Setup (session 4)
- Project: `march-madness-llm` (ID: `fdc5cddf-0304-448e-ba40-7cace6062dab`)
- Org: `Admin Org` (ID: `35f6dba3-225e-494b-9a09-e2196134d87e`)
- Environments: `dev`, `staging`, `prod` (default ones created automatically)
- Machine identity: `march-madness-ci` (ID: `b54463a2-0356-4a2f-be2c-0c32b657ec68`)
- **Universal Auth Client ID**: `2b77eb19-49b6-4718-8ba7-5c5eb4e4a36b` (in GitHub secret + Coolify)
- **Universal Auth Client Secret**: stored in GitHub secret `INFISICAL_CLIENT_SECRET` + Coolify env

### Docker Auth Flow (session 4)
- `backend/entrypoint.sh` — gets a fresh machine identity token on each container start
  - Calls `POST /api/v1/auth/universal-auth/login` with client creds
  - Sets `INFISICAL_TOKEN` env var, then runs `infisical run`
- Docker container needs: `INFISICAL_CLIENT_ID` + `INFISICAL_CLIENT_SECRET`
- **No longer uses a static INFISICAL_TOKEN** (which would expire)

### Infisical Admin API Bootstrap (session 4)
- First user signup via: `POST /api/v1/admin/signup` (no email verification needed)
- Login flow: `POST /api/v3/auth/login` → get initial token, then `POST /api/v3/auth/select-organization` → org-scoped token
- Secret creation: `POST /api/v3/secrets/raw/:secretName` with `workspaceId`, `environment`, `secretValue`

### Infisical CLI in Docker (session 3)
- The APT setup.deb.sh fails on Debian 13 (trixie) — package not found
- Binary URL format: `https://github.com/Infisical/cli/releases/download/v{VERSION}/cli_{VERSION}_linux_amd64.tar.gz`
- Currently pinned to v0.43.58 in backend/Dockerfile
- **To upgrade**: update the version in backend/Dockerfile AND ci.yml

### inviteOnlySignup workaround (session 4)
- Self-hosted Infisical defaults to `inviteOnlySignup: true` even with `INVITE_ONLY_SIGNUP=false`
- Works around it: `POST /api/v1/admin/signup` endpoint bypasses this restriction
- After first user created, `initialized: t` in `super_admin` table — prevents re-use

### Umami Analytics (session 3)
- Umami at `analytics.drose.io` (container `umami-es84cow0os8kc80wgkg0g408`)
- Website ID: `680a2d09-14dd-45d7-8b03-32cbcf459d12`
- Stale Caddy route fix (if it breaks again):
  - Find route with `upstreams.dial = 172.18.0.1:3000` for host `analytics.drose.io`
  - Delete: `docker exec coolify-proxy curl -sX DELETE http://localhost:2019/config/apps/http/servers/srv0/routes/INDEX`

### Coolify App Config (r0w0c0s)
- Env vars currently set:
  - `BACKEND_URL`: https://api.marchmadness.drose.io (build-time)
  - `BACKEND_PORT`: 50000
  - `FRONTEND_PORT`: (default 3000)
  - `INFISICAL_CLIENT_ID`: machine identity client ID (runtime)
  - `INFISICAL_CLIENT_SECRET`: machine identity client secret (runtime)

---

## Decisions Made

- **Self-hosted Infisical** at `secrets.drose.io` (moved from cloud, no rate limits)
- **Machine identity (Universal Auth)** instead of service tokens (don't expire)
- **entrypoint.sh** pattern for Docker — gets fresh token on each startup
- **Infisical Cloud → self-hosted migration**: all secrets migrated, cloud project still exists but unused
- **Keep CRA** — don't migrate to Vite/Next.js with 12 days to tournament
- **Playwright over Cypress** — first-class `routeWebSocket()` support
- **No features for 2026** — polish and reliability only
- **Skip 2026 bracket update** — stick with 2024 data until after Selection Sunday (March 15)

---

## Next Steps (priority order)

### 1. After March 15: bracket data
- Replace `backend/data/bracket_2024.json` with 2026 field
- Update `frontend/src/team_mappings.ts` for any new teams
- Verify logos exist for all 64 teams in `frontend/public/logos/optimized/50x50/`
- Full E2E test run with real data

### 2. Monitor Caddy routing for analytics.drose.io
- If Grafana starts showing at analytics.drose.io again, re-run the Caddy API delete fix

### 3. Infisical admin password
- Stored during bootstrap — check macOS Keychain `infisical-admin-march-madness`

---

## Reference

| Item | Location |
|------|----------|
| Backend source | `backend/mm_ai/` |
| Frontend source | `frontend/src/` |
| Infisical instance | https://secrets.drose.io (self-hosted on clifford) |
| Infisical service | Coolify: `ncs84sgckcs08c4wsc0ogwwo` |
| Infisical project ID | `fdc5cddf-0304-448e-ba40-7cace6062dab` |
| Client ID (Keychain) | `infisical-march-madness-client-id` (account: `march-madness-llm`) |
| Client secret (Keychain) | `infisical-march-madness-client-secret` (account: `march-madness-llm`) |
| Playwright tests | `frontend/e2e/` |
| Visual baselines | `frontend/e2e/visual.spec.ts-snapshots/` |
| Run backend locally | `infisical run --env dev --domain https://secrets.drose.io -- uv run uvicorn mm_ai.main:app --reload --port 8000` |
| Run frontend locally | `infisical run --env dev --domain https://secrets.drose.io -- bun run start` |
| Run backend tests | `infisical run --env dev --domain https://secrets.drose.io -- uv run pytest` |
| First-time login (local) | `infisical login --method=universal-auth --client-id=<from-keychain> --client-secret=<from-keychain> --domain=https://secrets.drose.io` |
| Regen visual baselines | `bunx playwright test --update-snapshots` (requires running dev server) |
| Uptime monitor | https://stats.uptimerobot.com/Jlo4zDIBm8 |
| Umami website ID | `680a2d09-14dd-45d7-8b03-32cbcf459d12` |
| Infisical CLI repo | https://github.com/Infisical/cli |
