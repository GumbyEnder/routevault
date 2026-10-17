# Deploy

Canonical code: `/mnt/nas/agents/Projects/RouteVault/code/routevault-staging/`

## Live (v1a accounts + v0.2 catalog)

**URL:** https://routevault-production.up.railway.app  
**Railway project:** `routevault` (`37267b3e-5395-431d-beda-f1982c9fb32c`)  
**Service:** `routevault` (`92a18c91-f43b-46ad-87bd-82c0e281a53e`)  
**Environment:** `production` (`b5923162-e36a-40d3-8e96-f6d1094f264f`)  
**Dashboard:** https://railway.com/project/37267b3e-5395-431d-beda-f1982c9fb32c

## Refresh live prices (before redeploy)

```bash
bash /mnt/nas/agents/Projects/RouteVault/scripts/tick.sh
# 4×/day job: live OpenRouter prices + new-model discovery + AI/tech news, then railway up
# prices-only (no news, no discover, no deploy):
#   bash /mnt/nas/agents/Projects/RouteVault/scripts/refresh.sh
```

## Price history

- Live snapshot: OpenRouter `/api/v1/models` (today).
- History: weekly series from [jvrck/openrouterlist](https://github.com/jvrck/openrouterlist) `data/history/prices.json`, from `first_seen` up to 183 days. Not a synthetic walk. Models that launched last week only have last week.

## Redeploy from NAS

```bash
cd /mnt/nas/agents/Projects/RouteVault/code/routevault-staging
railway up --detach -m "describe change"
# poll until SUCCESS:
railway deployment list --json
```

First-time / new machine (if not linked):

```bash
cd /mnt/nas/agents/Projects/RouteVault/code/routevault-staging
railway link --project 37267b3e-5395-431d-beda-f1982c9fb32c --environment production --service routevault
railway up --detach -m "..."
```

## Other hosts (optional)

- GitHub Pages via `.github/workflows/pages.yml` (deploys `code/routevault-staging`)
- Cloudflare Pages pointing at the same folder

## Local preview

```bash
cd code/routevault-staging && python3 -m http.server 8765
```

## Data honesty

Price history in SQLite/`models.json` is **synthetic demo data** until real ingest ships.
Site banner already labels this on index/models.
