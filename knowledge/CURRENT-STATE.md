# RouteVault — Current State

**Last updated:** 2026-07-17 (NAS handoff)

## Code Repository

**Path:** `/mnt/nas/agents/Projects/RouteVault/code/routevault-staging`

### Pages Status

| Page | Visual | Functional | Notes |
|------|--------|------------|-------|
| `index.html` | High | Medium | Marketing landing |
| `quiz.html` | High | Good | Loads `models.json` + scoring |
| `models.html` | High | Low-Medium | List; limited intelligence |
| `model-detail.html` | High | Good | Chart.js price history |
| `harness-detail-hermes.html` | Medium | Low | Placeholder |
| `pricing.html` | High | Low | Marketing |
| `ecosystem.html` | High | Low | Marketing |
| `how-we-score.html` | High | Low | Thin |
| `admin-dashboard.html` | Medium | Low | Placeholder |

### Data Layer

- **SQLite:** `/mnt/nas/agents/Projects/RouteVault/data/routevault.db` — 17 models, 1530 price_history rows  
- **Export:** `data/models.json` (also under staging `data/`)  
- **Seed script:** `data/init_db.py` — **synthetic** 90d prices  
- **Generated_at on JSON:** 2026-05-14 (stale)

### Maturity

| Area | Score |
|------|-------|
| Visual / Design | 8/10 |
| Data Foundation | 6/10 (real schema; demo content) |
| Intelligence | 3/10 |
| Production Readiness | 2/10 (NAS consolidated; not deployed) |

**Bottom line:** Excellent mock foundation; next value is **public static deploy**, then real data.

## Obsidian

`/mnt/nas/Obsidian Vaults/Main Vault/01_Projects/RouteVault/`  
SoT + Go-Live written 2026-07-17.
