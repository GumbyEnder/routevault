---
status: active
owner: GumbyEnder
created: 2026-07-17
last-reviewed: 2026-07-17
tags: [routevault, go-live, handoff]
---

# RouteVault — 01 Go-Live Plan (v0)

**Objective:** Public URL live **soon**, with an honest static site. Not full router SaaS.

**Canonical code:** `/mnt/nas/agents/Projects/RouteVault/code/routevault-staging/`  
**SoT:** [[00-Source-of-Truth]]

---

## Scope lock — v0 (IN)

| # | Deliverable | Notes |
|---|-------------|--------|
| 1 | Static hosting of current HTML/JS site | index, models, model-detail, quiz, how-we-score, pricing, ecosystem as-is or lightly cleaned |
| 2 | HTTPS public URL | Prefer `routevault.ai`; interim OK (`*.pages.dev`, `*.vercel.app`, etc.) |
| 3 | Working relative paths for `data/models.json` | Verify charts + quiz after deploy |
| 4 | Data honesty banner | One-line: pricing history is illustrative / demo until pipeline is live |
| 5 | Production git remote | Forgejo primary + GitHub mirror (house rule) |
| 6 | README deploy section | How to re-deploy from NAS path |

## Scope lock — v0 (OUT)

- Live model router / OpenRouter proxy  
- User accounts / auth (login/register can stay as non-linked placeholders or hidden)  
- User weighting sliders  
- Real scraped multi-year price history (optional stretch: one-shot price refresh)  
- Hermes deep integration  
- Admin dashboard as a real product surface  

---

## Definition of Done (v0)

- [ ] Site reachable on public HTTPS without VPN  
- [ ] `/` loads; `/models.html` lists models; `/model-detail.html` chart does not 404 JSON  
- [ ] Quiz loads models (or degrades gracefully)  
- [ ] Footer or banner states data is demo/illustrative if still synthetic  
- [ ] Repo on Forgejo (and GitHub mirror) contains the staged site  
- [ ] [[00-Source-of-Truth]] updated with live URL + remote URLs  
- [ ] Kanban: “Create production deploy” moved to Done  

---

## Execution phases

### Phase A — Local/NAS preview (30–60 min)

```bash
cd "/mnt/nas/agents/Projects/RouteVault/code/routevault-staging"
python3 -m http.server 8765
# Browse: home, models, model-detail?id=..., quiz
```

Fix any broken relative paths to `data/models.json` before deploy.

Optional polish (same day):

- Add demo-data banner on `index.html` + `models.html`  
- Hide or relabel admin/login if they confuse visitors  
- Refresh `models.json` timestamps only if you also refresh prices  

### Phase B — Git remotes (1–2 hr)

1. Create repo `routevault` (or `routevault-web`) on **Forgejo** (primary).  
2. Mirror on **GitHub** as GumbyEnder.  
3. From NAS tree:

```bash
cd /mnt/nas/agents/Projects/RouteVault
# If not already a git repo:
git init
git add code/routevault-staging data docs knowledge pipeline README.md
git commit -m "RouteVault v0 static site + data seed for public deploy"
# add forgejo + github remotes; push main
```

**CIFS note:** `git` on CIFS can be slow/fragile. If git init fails or locks, clone to local disk, copy tree, push, then document that dev clones are local but **canonical snapshot remains on NAS**.

### Phase C — Host static site (1–2 hr)

Pick one (all available on gumbyender machine tools; other agent may use same):

| Host | Fit | Notes |
|------|-----|--------|
| **Cloudflare Pages** | Best default | Drag/CLI upload `code/routevault-staging`; free HTTPS |
| **Vercel** | Good | Static; `vercel` CLI present on primary host |
| **Netlify** | Good | `netlify` CLI present |
| **NAS + Caddy/Tailscale only** | Not “public live” | Fine for private preview only |

**Recommended:** Cloudflare Pages project `routevault` → attach custom domain when DNS ready.

Deploy root directory must be **`code/routevault-staging`** (includes `data/models.json`).

### Phase D — Domain

1. Confirm registrar ownership of `routevault.ai` (or choose alternate).  
2. Point DNS per host instructions (CNAME to Pages/Vercel).  
3. Update SoT with final URL.

If domain not ready: ship on `*.pages.dev` / `*.vercel.app` the same day; swap domain later.

### Phase E — Post-launch (not blockers)

1. Real price ingest (OpenRouter / provider pages) → replace synthetic history  
2. Price Intelligence badges on `models.html`  
3. Benchmark columns from public sources  
4. Production repo README + weekly data refresh cron  
5. Smart router = Phase 2+ product, not v0  

---

## Suggested task order for takeover agent

1. ACK SoT + this plan; confirm NAS mount path exists on their machine.  
2. Phase A preview; file any path bugs.  
3. Phase B git remotes.  
4. Phase C deploy static.  
5. Phase D domain if available.  
6. Update SoT live URL + kanban Done.  
7. Report: public URL, remotes, residual risks.

---

## Risks

| Risk | Mitigation |
|------|------------|
| Synthetic prices misread as truth | Banner + README honesty |
| CIFS git/SQLite flakiness | Local clone for git push; local temp for DB writes |
| Domain not owned / not DNS-ready | Ship on provider subdomain first |
| Stale model list (May 2026 models) | Accept for v0 or one-shot refresh of seed list |
| Other agent can’t see `/mnt/nas` | Fail closed — do not invent alternate code home; fix mount |

---

## Success metric

An external browser can open the site and a technical user says:  
“I understand what RouteVault is and can browse models/prices” — not “this is production intelligence.”

---

*Created 2026-07-17 for cross-machine agent handoff. Keep in sync with [[00-Source-of-Truth]].*
