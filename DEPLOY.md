# Deploy

Canonical code: `/mnt/nas/agents/Projects/RouteVault/code/routevault-staging/`

## Public static host
- GitHub Pages via `.github/workflows/pages.yml`
- Preferred alternate: Cloudflare Pages project pointing at the same folder

## Local preview
```bash
cd code/routevault-staging && python3 -m http.server 8765
```

## Data honesty
Price history in SQLite/`models.json` is **synthetic demo data** until real ingest ships.
