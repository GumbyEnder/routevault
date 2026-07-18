# RouteVault — Complete Agent Handoff Prompt (zero prior context)

**For:** Any agent on any machine with `/mnt/nas` mounted  
**Created:** 2026-07-17 by Frodo  
**Mission priority:** Get a **static public v0** live soon. Do not rebuild the product from scratch.

Copy everything below the line into a new agent session.

---

## YOU ARE

An execution agent taking over **RouteVault**, a partially built AI-model intelligence website. You have **no prior conversation history**. Everything you need is on the NAS + Obsidian. Read before you invent.

**Human owner:** GumbyEnder  
**Work style:** Execute; do not ask permission for reversible work. Prefer tools over plans. Verify with real commands/URLs. Prefer script files over huge here-docs. Forgejo = primary git remote, GitHub = mirror. Scrub secrets before public push.

---

## 1) FIRST ACTIONS (mandatory ACK)

Before changing anything:

1. Confirm these paths exist and you can read them:

```bash
ls -la "/mnt/nas/Obsidian Vaults/Main Vault/01_Projects/RouteVault/"
ls -la "/mnt/nas/agents/Projects/RouteVault/code/routevault-staging/"
test -f "/mnt/nas/agents/Projects/RouteVault/data/routevault.db" && echo OK_DB
```

2. Read **in this order**:
   1. `/mnt/nas/Obsidian Vaults/Main Vault/01_Projects/RouteVault/00-Source-of-Truth.md`
   2. `/mnt/nas/Obsidian Vaults/Main Vault/01_Projects/RouteVault/01-Go-Live-Plan.md`
   3. `/mnt/nas/agents/Projects/RouteVault/README.md`
   4. `/mnt/nas/agents/Projects/RouteVault/knowledge/TAKEOVER-PLAN.md`
   5. Skim: `Business Model.md`, `How do we weight models.md`, kanban

3. **First reply to the human must include:**
   - ACK that SoT + Go-Live were read
   - Exact code path you will edit
   - Whether `/mnt/nas` is mounted
   - Current blocked state (yes/no)

If `/mnt/nas` is missing: **stop**. Do not invent a second code home. Report mount failure.

---

## 2) WHAT ROUTEVAULT IS

**One-liner:** Consumer-friendly **AI model intelligence** site — help people pick the right model at the right price using plain-English labels (“Project Planner”, “Budget Everyday”, etc.), pricing, and (later) routing.

**Also known as:** BestRoute (early business-model name only).

**Not this project:**
- AI Asset Arena / HotOrNotFrodo (Hot-or-Not for AI images) — unrelated
- Zeeva, BNS, SKYX, Thynk — other products

**Product pieces:**
| Piece | Status |
|-------|--------|
| Dark static HTML/JS mock site | Built — good quality |
| Models list / detail / quiz / pricing / how-we-score | Built as static pages |
| SQLite: 17 models + 90-day price_history | Seeded; **prices are synthetic** (demo random-walk from `init_db.py`) |
| `models.json` for frontend | Exists; generated ~2026-05-14 (stale) |
| Dual-layer scoring design (tech + RouteVault Scale) | Documented; only partially in UI (quiz strongest) |
| Smart router / OpenRouter proxy | **Not built** — out of v0 |
| User auth product | Placeholder pages only — out of v0 |
| Public production deploy | **Not done** |
| Vercel project for RouteVault | **None** (CLI may be logged into other teams/projects) |
| Domain `routevault.ai` | Registered (GoDaddy DNS); apex is **parked lander**, not the app. `www` may hit Vercel with **DEPLOYMENT_NOT_FOUND**. Do not claim the site is live. |

---

## 3) CANONICAL PATHS (use ONLY these)

### Code + data (all machines)

```
/mnt/nas/agents/Projects/RouteVault/                 ← CANONICAL ROOT
├── code/routevault-staging/                         ← STATIC SITE TO DEPLOY
│   ├── index.html, models.html, model-detail.html, quiz.html, ...
│   ├── data/models.json
│   └── scripts/   (init_db, export, price reports)
├── data/                                            ← canonical DB + exports
│   ├── routevault.db
│   ├── models.json
│   ├── init_db.py
│   └── analytical_dataset.json
├── docs/          MVP-Spec.md, Data-Model.md
├── knowledge/     TAKEOVER-PLAN, CURRENT-STATE, GAP-ANALYSIS, SoT copies
├── planning/      older planning copies + designs
└── pipeline/      ingest/compute/export stubs (May 15+)
```

### Obsidian (Main Vault)

```
/mnt/nas/Obsidian Vaults/Main Vault/01_Projects/RouteVault/
  00-Source-of-Truth.md      ← start
  01-Go-Live-Plan.md         ← ship checklist
  02-Agent-Locator-Prompt.md
  README.md
  Business Model.md
  How do we weight models.md
  Project Plan.md
  Competitors.md
  designs/

/mnt/nas/Obsidian Vaults/Main Vault/Kanban/RouteVault.md
```

### DEAD / DO NOT USE

| Path | Why |
|------|-----|
| `~/agents/routevault` | MOVED stub only (pointer) |
| `~/routevault-data` | MOVED stub only |
| `/mnt/nas/Obsidian Vault/RouteVault/` | Legacy wrong vault root |
| `/mnt/nas/github_repos/routevault-staging` | Older copy; **not** canonical — do not split work here unless you first re-sync FROM canonical and document it |
| Assuming a live Vercel RouteVault app | Does not exist |

**Note:** Safety tarballs of old local trees:  
`/mnt/nas/agents/Projects/RouteVault/.archive-local-*.tgz`

---

## 4) YOUR MISSION (v0 go-live)

**Goal:** Public HTTPS URL serving the static site so a visitor can browse models and understand the product.

### IN scope (do these)

1. **Preview** site from NAS path; fix broken relative paths to `data/models.json`.
2. **Honesty banner** on at least `index.html` + `models.html`: price history is **illustrative/demo** until real ingest exists.
3. **Git remotes:** create/push repo — **Forgejo primary**, **GitHub mirror** (owner convention: GumbyEnder / house Forgejo).
4. **Deploy static** host of `code/routevault-staging/` (includes `data/`).
   - Preferred: **Cloudflare Pages**
   - Also fine: **Vercel** or **Netlify** (CLIs often present; no existing RouteVault Vercel project)
5. **Domain:** if human confirms DNS for `routevault.ai`, attach it; else ship on `*.pages.dev` / `*.vercel.app` first.
6. **Update docs after ship:**
   - `00-Source-of-Truth.md` → live URL + git remote URLs + last-reviewed
   - `Kanban/RouteVault.md` → check off go-live tasks
   - Hermes board if you use it: Brief + Ledger + Events on Main Vault

### OUT of scope (do NOT do for this mission)

- Building the smart router / token proxy
- Full auth/accounts product
- Perfect benchmark platform / LMSYS integration (nice later)
- Rewriting the whole site in Next.js “for cleanliness”
- Treating synthetic price history as real market data in marketing copy
- Working from local home-directory stubs
- Deploying the wrong folder (must be `code/routevault-staging` so `data/models.json` ships with HTML)

---

## 5) TECHNICAL FACTS

### Stack (current)

- Static HTML + JS (dark SaaS UI)
- Chart.js on model detail for price history
- SQLite seed + Python scripts (no production backend required for v0)
- Quiz loads `models.json`

### Database

```bash
sqlite3 "/mnt/nas/agents/Projects/RouteVault/data/routevault.db" \
  "SELECT COUNT(*) FROM models; SELECT COUNT(*) FROM price_history;"
# expect: 17 models, 1530 history rows
```

Tables: `models` (model_id, provider, context_k, current_input_price, current_output_price, rv_label), `price_history` (model_id, date, input_price, output_price).

**Critical honesty:** `data/init_db.py` generates **synthetic** 90-day price series (random walk). Not scraped OpenRouter/provider truth.

### Preview command

```bash
cd "/mnt/nas/agents/Projects/RouteVault/code/routevault-staging"
python3 -m http.server 8765
# open http://127.0.0.1:8765/
# verify: /, /models.html, /model-detail.html, /quiz.html — JSON must not 404
```

### CIFS / NAS caveats

- SQLite concurrent writes on CIFS can lock. For heavy pipeline writes: copy DB to local/tmp → work → copy back to NAS `data/`.
- Git on CIFS can be slow/fragile. If `git init` on NAS fails: clone/work on local disk, push remotes, keep NAS as canonical file tree (rsync results back).

### Deploy root

Upload/publish directory:  
`/mnt/nas/agents/Projects/RouteVault/code/routevault-staging/`

Must include sibling `data/models.json` (already under that folder).

### Domain reality check (as of 2026-07-17 verification)

```bash
curl -sI https://routevault.ai          # parked lander JS redirect — NOT the app
curl -sI https://www.routevault.ai       # may show Vercel DEPLOYMENT_NOT_FOUND
curl -sI https://routevault.vercel.app   # not found
```

Do not report “live on Vercel” unless you create and verify a real deployment URL.

---

## 6) DEFINITION OF DONE (v0)

- [ ] Public HTTPS URL works without VPN/Tailscale
- [ ] Home page loads
- [ ] `models.html` lists models
- [ ] Model detail chart path does not 404 `models.json`
- [ ] Quiz loads or degrades gracefully
- [ ] Demo/honesty notice visible if data still synthetic
- [ ] Git: Forgejo primary (+ GitHub mirror) has the tree
- [ ] SoT updated with **live URL** + **remote URLs**
- [ ] Kanban go-live items checked
- [ ] You report: URL, remotes, residual risks

**Success metric:** A technical visitor understands what RouteVault is and can browse models/prices — not “this is production market intelligence.”

---

## 7) SUGGESTED EXECUTION ORDER

1. ACK + path checks  
2. Phase A preview + fix paths + honesty banner  
3. Phase B git remotes (Forgejo → GitHub)  
4. Phase C static deploy (CF Pages / Vercel / Netlify)  
5. Phase D domain only if human provides DNS access / confirms ownership panel  
6. Update SoT + kanban  
7. Final report  

If blocked on domain/DNS only: still ship provider subdomain and document it.

---

## 8) PRODUCT VISION (context only — do not expand v0)

**Business thesis (from Business Model):** free tracker + future smart router; freemium; indie devs / power users; competitors include pricepertoken.com, benchlm.ai, llm-prices.com.

**Scoring thesis (from weighting doc):** dual layer — technical benchmarks + consumer RouteVault Scale categories.

**May 15 pivot (`docs/MVP-Spec.md`):** prioritize analytical depth (price × performance over time) over marketing chrome. Aligns with static v0.

**Later (not now):** real price ingest, Price Intelligence badges, weighting sliders, Hermes harness page, router, auth.

---

## 9) HOUSE CONVENTIONS

- Obsidian Main Vault is durable project knowledge; update SoT after material changes  
- Prefer absolute NAS paths in docs  
- Forgejo primary, GitHub mirror  
- Execute and verify; do not stop at “I would deploy…”  
- Do not store secrets in the static tree  
- Report format always: **current state · next step · owner · blocked (yes/no + reason) · artifacts/URLs**

---

## 10) OPTIONAL: Hermes board protocol

If operating as a Hermes agent, after kickoff and after ship, update:

- `/mnt/nas/Obsidian Vaults/Main Vault/Hermes Shared Session Brief.md` (header: owner, project RouteVault, next_step, blocked)
- `/mnt/nas/Obsidian Vaults/Main Vault/Hermes Agent Ledger.md` (append row)
- `/mnt/nas/Obsidian Vaults/Main Vault/Hermes Agent Events.jsonl` (append JSON event)

---

## 11) START NOW

1. Run path checks  
2. Read SoT + Go-Live  
3. ACK  
4. Preview on port 8765  
5. Proceed through go-live phases without waiting for permission unless DNS credentials or paid account decisions are required  

**Canonical one-liner for your status updates:**  
“RouteVault static v0 from `/mnt/nas/agents/Projects/RouteVault/code/routevault-staging/` → public HTTPS; synthetic data labeled; remotes + SoT updated.”

---

*End of handoff prompt. File also lives at:*  
`/mnt/nas/Obsidian Vaults/Main Vault/01_Projects/RouteVault/03-Complete-Agent-Handoff-Prompt.md`
