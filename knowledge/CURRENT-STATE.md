# RouteVault — Current State

**Last updated:** 2026-10-05

## Live

https://routevault.ai (Astro SSR app, service `routevault-web`) · legacy static fallback at https://routevault-production.up.railway.app

## 2026-10-05 — Trends visualizations + scoring fix

- `/trends` is now server-rendered with charts: stat tiles, 30-day price-mover bars, rebased multi-line price history for top movers, Scale-tier value-score bars (`trendsData()` in `src/lib/db.js`).
- db.js fixes: benchmark pivot now maps `tool_use`/`general_intelligence` (was pivoting on nonexistent type names — tool-use and general contributed 0 everywhere), and the value-score formula matches the static-site rubric (32/25/18/15/7 weights over 100, general falls back to reasoning). Value scores rose where tool-use/context exist — intentional, rubric alignment.
- Explorer Reason/Code columns now populate (143/180 models).
- Cloudflare purge helper: `/mnt/nas/host-ops/routevault-purge-cf.sh`.

## What shipped in v0.2

- Live OpenRouter prices + Artificial Analysis indexes (30 curated models)
- SQLite + `dataset.json` export via `python3 -m pipeline.run`
- Explorer with sliders, Trends, Model detail, Quiz, My Stack, Route resolver
- Honesty: prices live; history is ingest-accumulated (OpenRouterList weekly tape + live snapshot)
- Router is a published-floor resolver, not a token proxy
- **v1a accounts live:** email/password, HttpOnly `rv_session`, Railway Postgres
- Signed-in users sync Stack / weights / alerts / resolves; guests keep localStorage
- First-login merge: keep local / use cloud / union
- Password-reset API exists; email delivery is not wired (v1b)

## 4×/day tick (2026-09-21)

Hermes cron, every 6 hours, `no_agent`, script:

`/mnt/nas/agents/Projects/RouteVault/scripts/tick.sh`

Each run:

1. Live OpenRouter prices into SQLite `price_history` / `models`
2. Scan full OpenRouter catalog; store unseen in `discovered_models`; auto-ingest up to 40 with AA indexes
3. AI/tech RSS (politics-filtered) into `news_items`
4. Export `dataset.json`, `news.json`, `discovered_models.json`
5. `railway up` the staging site (set `ROUTEVAULT_DEPLOY=0` to skip)

Public:

- `GET /api/news`
- `GET /api/discoveries`
- `/api/health` includes `news` count

## Next product cut

**v1b later** — Pro gate, email alerts, Team. Do not start until asked.

## Refresh

`bash scripts/tick.sh`  
or prices-only: `bash scripts/refresh.sh` then `railway up` from `code/routevault-staging/`
