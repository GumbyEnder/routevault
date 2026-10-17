# RouteVault

**Canonical root (all machines with NAS):** `/mnt/nas/agents/Projects/RouteVault/`

**Obsidian Source of Truth:**  
`/mnt/nas/Obsidian Vaults/Main Vault/01_Projects/RouteVault/00-Source-of-Truth.md`

**Go-live plan:**  
`/mnt/nas/Obsidian Vaults/Main Vault/01_Projects/RouteVault/01-Go-Live-Plan.md`

## Project Goal

RouteVault is a research & analysis / consumer intelligence product for AI models: price history, benchmarks, RouteVault Scale labels, recommendations. Near-term: **static public v0**. Later: smart router.

## Folder Structure

```
RouteVault/
├── README.md                 # this file
├── code/
│   └── routevault-staging/   # static site to deploy
├── data/                     # routevault.db, models.json, init_db.py
├── docs/                     # MVP-Spec, Data-Model
├── knowledge/                # TAKEOVER-PLAN, CURRENT-STATE, GAP-ANALYSIS
├── planning/                 # early planning copies + designs
└── pipeline/                 # ingest / compute / export
```

## Important Documents

**Start here (Obsidian):** `00-Source-of-Truth.md`  
**Start here (repo):** `knowledge/TAKEOVER-PLAN.md`  
**Ship:** Obsidian `01-Go-Live-Plan.md`

## Quick preview

```bash
cd /mnt/nas/agents/Projects/RouteVault/code/routevault-staging
python3 -m http.server 8765
```

## Data note

`data/routevault.db` price history is a **synthetic seed** (see `data/init_db.py`). Label as demo on public v0 until real ingest lands.

## Migration note (2026-07-17)

Previously lived at `~/agents/routevault` and `~/routevault-data` on one host. **Moved entirely to this NAS path** so any agent on any machine with `/mnt/nas` can work. Local stubs remain as MOVED.md pointers only.

Safety tarballs: `.archive-local-*.tgz` in this directory.

---

*Last updated: 2026-08-13 (Railway v0 deploy).*

## Deploy (static v0)

**Live:** https://routevault-production.up.railway.app  
**Publish directory:** `code/routevault-staging/` (must include `data/models.json`)

```bash
cd /mnt/nas/agents/Projects/RouteVault/code/routevault-staging
python3 -m http.server 8765   # local preview
railway up --detach -m "..."  # redeploy to Railway
```

**Host:** Railway project `routevault` (see `DEPLOY.md`).  
**GitHub Pages:** workflow at `.github/workflows/pages.yml` (optional alternate).  
**Remotes:** Forgejo primary (house), GitHub mirror `https://github.com/GumbyEnder/routevault`.

Price history is **synthetic demo data** — labeled in the site banner.
