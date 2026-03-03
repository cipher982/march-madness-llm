# March Madness LLM - Vision & Roadmap

## What This Is

A web app that simulates NCAA March Madness tournament brackets using AI (LLM), seed logic, or randomness. Users watch brackets fill in real-time via WebSocket streaming with animated bracket visualization.

## What This Is NOT

- Not a bracket contest platform (ESPN/Yahoo/CBS own that)
- Not a betting tool
- Not trying to be the most accurate predictor
- Not a year-round product

## Target Audience

Casual fans and tech-curious people who want to:
1. See what AI thinks about the tournament
2. Generate fun brackets with custom preferences ("pick teams with animal mascots")
3. Share AI-generated brackets with friends
4. Use it as a conversation starter during March Madness

## Value Proposition (Honest Assessment)

**The hard truth:** A user can paste the bracket into ChatGPT and get a comparable result. The differentiation must come from:

1. **Experience** - Real-time animated bracket filling is fun to watch. ChatGPT gives a text list.
2. **Frictionless** - One click, watch it unfold. No prompt engineering needed.
3. **Shareability** - Visual bracket output is shareable. ChatGPT text isn't.
4. **Customization** - "Pick teams with the best mascots" is a delight feature.

**What would make it truly differentiated (future, not now):**
- Real stats integration (KenPom/Torvik efficiency ratings)
- Pool-optimized brackets ("I'm in a 200-person pool with upset scoring")
- Multiple bracket portfolio generation (chalk, balanced, chaos)
- Export to ESPN/Yahoo format

## 2026 Tournament Goals

### Must Have (Ship by March 15)
- [ ] 2026 bracket data loaded (after Selection Sunday)
- [ ] Robust test suite (backend unit + integration, frontend E2E)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Production-ready Docker builds (no dev servers)
- [ ] Error handling hardened (WebSocket, OpenAI API, data validation)
- [ ] Type safety (Python type hints, all React components as .tsx)
- [ ] Basic analytics (Umami)

### Should Have
- [ ] Visual regression testing (Playwright screenshots)
- [ ] Rate limiting on simulation endpoint
- [ ] LLM provider flexibility (z.ai for dev, configurable for prod)
- [ ] Improved UI polish (responsive, accessibility)
- [ ] Health endpoint that actually works

### Won't Do (2026)
- Real stats integration (KenPom/Torvik)
- Pool optimization features
- ESPN/Yahoo export
- User accounts or saved brackets
- Multiple simultaneous bracket display
- Mobile app

## Architecture Decisions

### LLM Strategy
**Current:** 63 sequential gpt-4o-mini calls per bracket (~$0.002/bracket)
**Future consideration:** Single-prompt bracket generation (1 call, structured output)
**For dev/testing:** Use z.ai (GLM-5) - flat rate, no per-token cost

The 63-call approach is fine for current scale. At viral scale (10K+ brackets/day), switch to single-prompt. Cost is not the blocker - reliability and latency are.

### Testing Philosophy
"I can't be the QA team" - the agent dev team must be self-sufficient:
- **Backend unit tests** validate bracket logic without any LLM calls
- **Backend integration tests** validate WebSocket flow with mocked LLM
- **Frontend E2E** (Playwright) validates full user flow with mocked WebSocket
- **Visual regression** catches UI breakage via screenshot comparison
- **CI gates** prevent merging broken code

### Frontend Migration Path
Current state: mixed JS/TSX mess from CRA era.
Plan: Convert all .js components to .tsx incrementally. Don't rewrite to Vite/Next.js - not worth the risk this close to tournament.

## Cost Model

| Scale | Brackets/day | Monthly LLM Cost | Notes |
|-------|-------------|-------------------|-------|
| Personal | 1-10 | $0.66 | Current state |
| Moderate | 100 | $6.60 | Shared with friends |
| Popular | 1,000 | $66 | HN/Reddit post |
| Viral | 10,000 | $660 | Need rate limiting |

Infrastructure (Coolify VPS) is fixed cost - already paid for.

## Non-Goals

- Monetization (this is a portfolio/fun project)
- Year-round engagement
- Competing with ESPN/CBS bracket platforms
- Perfect prediction accuracy
