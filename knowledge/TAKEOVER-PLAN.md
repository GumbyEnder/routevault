# RouteVault Takeover Plan

**Project:** RouteVault (AI Model Intelligence + future Smart Router)  
**Status:** Phase 1 complete (strong mockups) → Early Phase 2 (data) → **Handoff for public v0**  
**Last Updated:** 2026-07-17  
**Owner:** GumbyEnder + takeover agent  

**Canonical code root:** `/mnt/nas/agents/Projects/RouteVault/`  
**Obsidian SoT:** `/mnt/nas/Obsidian Vaults/Main Vault/01_Projects/RouteVault/00-Source-of-Truth.md`  
**Go-live:** `/mnt/nas/Obsidian Vaults/Main Vault/01_Projects/RouteVault/01-Go-Live-Plan.md`

---

## Executive Summary

RouteVault helps users choose AI models by price + capability signals, with consumer-friendly RouteVault Scale labels. Phase 1 static site is strong; intelligence is partial; **no public deploy yet**.

**Immediate mission for takeover agent:** Execute **v0 static go-live** (preview → git remotes → host → URL in SoT). Do **not** build the router for first ship.

---

## Current State (2026-07-17)

### What exists and is strong

**Code:** `/mnt/nas/agents/Projects/RouteVault/code/routevault-staging/`

- Dark SaaS static pages: index, quiz, models, model-detail, pricing, ecosystem, how-we-score, harness placeholder, admin/auth shells
- SQLite + export: `data/routevault.db` (17 models, 1530 price rows), `data/models.json`
- Quiz data-driven; model-detail Chart.js history
- Pipeline stubs under `pipeline/`

**Obsidian:** `/mnt/nas/Obsidian Vaults/Main Vault/01_Projects/RouteVault/`

- `00-Source-of-Truth.md`, `01-Go-Live-Plan.md`, Business Model, weighting, Project Plan, kanban

### What is weak / missing

- Synthetic price history (not market truth)
- Benchmarks not in DB/UI
- No production deploy / confirmed domain wiring
- No Forgejo/GitHub remotes confirmed
- Router not built (correctly out of v0 scope)

### Dead paths (do not use)

- `/home/*/agents/routevault` (MOVED stubs only)
- `/home/*/routevault-data` (MOVED stubs only)
- `/mnt/nas/Obsidian Vault/RouteVault/`
- `/mnt/nas/github_repos/routevault-staging` as assumed home

---

## Vision vs Reality (abbrev)

| Vision | Reality | v0 action |
|--------|---------|-----------|
| Dual-layer scoring | Partial (quiz) | Ship as-is; improve later |
| Price Intelligence | Detail page only | Banner honesty; badges later |
| Smart router | None | **Out of v0** |
| routevault.ai live | Not deployed | **Primary goal** |

---

## Phased Roadmap

### Now — v0 Go-Live (this handoff)

See Obsidian `01-Go-Live-Plan.md`: preview → git → static host → domain/URL.

### Phase 2A — Make data real

- Price change indicators on models page  
- Real ingest replacing synthetic history  
- Scoring visible outside quiz  

### Phase 2B — User control

- Weighting sliders, My Stack, stronger filters  

### Phase 2C — Router & production product

- Smart router, auth, BYOK proxy (Workers/Fly)  

---

## Working rules

1. Edit only under `/mnt/nas/agents/Projects/RouteVault/` + Obsidian RouteVault paths.  
2. SQLite writes: prefer local temp copy if CIFS locks.  
3. Forgejo primary, GitHub mirror.  
4. Update SoT + kanban after deploy.  
5. First message: ACK SoT + Go-Live + code path.

---

## Open questions (for human if blocked)

- Is `routevault.ai` owned and which DNS panel?  
- Preferred host: Cloudflare Pages vs Vercel vs Netlify?  
- Ship synthetic data with banner, or block launch until one price refresh?

**Default if human unavailable:** Cloudflare Pages + provider subdomain + demo banner.

---

*This file is the in-repo takeover companion to Obsidian SoT. Update both when paths or live URL change.*
