---
status: active
owner: GumbyEnder
steward_agent: any (NAS-shared)
created: 2026-05-02
last-reviewed: 2026-08-14
tags: [project, routevault, source-of-truth, handoff]
---

# RouteVault — 00 Source of Truth

**Status:** v1a live on Railway · accounts + cloud sync · live OpenRouter prices + AA indexes · router is resolver-only  
**Goal (near-term):** Keep Railway durable host; attach custom domain `routevault.ai` when DNS ready. v1b later.  
**Product:** Consumer-friendly AI model intelligence — scores, prices, history, recommendations; future smart router.

---

## Read order (mandatory for any agent)

1. **This file** (paths, status, constraints)
2. [[01-Go-Live-Plan]] — scope lock + deploy DoD for v0
3. `/mnt/nas/agents/Projects/RouteVault/knowledge/TAKEOVER-PLAN.md` — detailed takeover
4. `/mnt/nas/agents/Projects/RouteVault/docs/MVP-Spec.md` — analytical MVP (May 15 pivot)
5. [[How do we weight models]] + [[Business Model]] — product thesis
6. `docs/USER-MANAGEMENT-V1A.md` — locked accounts cut (next product work)
7. [[Kanban/RouteVault]] — task board

**ACK rule:** First reply from a takeover agent must confirm they read this SoT + Go-Live plan and state the exact code path they will edit.

---

## Canonical locations (NAS only — all machines)

| What | Absolute path |
|------|----------------|
| **Code + data + pipeline (canonical)** | `/mnt/nas/agents/Projects/RouteVault/` |
| **Static site (ship this)** | `/mnt/nas/agents/Projects/RouteVault/code/routevault-staging/` |
| **SQLite + JSON data** | `/mnt/nas/agents/Projects/RouteVault/data/` |
| **Pipeline scripts** | `/mnt/nas/agents/Projects/RouteVault/pipeline/` |
| **In-repo knowledge** | `/mnt/nas/agents/Projects/RouteVault/knowledge/` |
| **Obsidian project notes** | `/mnt/nas/Obsidian Vaults/Main Vault/01_Projects/RouteVault/` |
| **Kanban** | `/mnt/nas/Obsidian Vaults/Main Vault/Kanban/RouteVault.md` |

### Local machine stubs (do not develop here)

| Old local path | Status |
|----------------|--------|
| `~/agents/routevault/` | **MOVED** → NAS; only `MOVED.md` pointer |
| `~/routevault-data/` | **MOVED** → NAS `data/`; only `MOVED.md` pointer |

Archives (safety tarballs on NAS, 2026-07-17):  
`/mnt/nas/agents/Projects/RouteVault/.archive-local-*.tgz`

### Dead / do-not-use paths

- `/mnt/nas/Obsidian Vault/RouteVault/` (legacy vault root — wrong)
- `/mnt/nas/github_repos/routevault-staging` (may not exist; not canonical)
- Any path under `/home/<user>/agents/routevault` **except** the MOVED stub

---

## Repository tree (canonical)

```
/mnt/nas/agents/Projects/RouteVault/
├── README.md
├── code/
│   └── routevault-staging/     # static HTML/JS site + scripts/
│       ├── index.html, models.html, model-detail.html, quiz.html, ...
│       ├── data/models.json
│       └── scripts/            # init_db, export, price reports + local db copy
├── data/                       # canonical DB + exports
│   ├── routevault.db
│   ├── models.json
│   ├── init_db.py
│   └── analytical_dataset.json
├── docs/                       # MVP-Spec, Data-Model
├── knowledge/                  # TAKEOVER-PLAN, CURRENT-STATE, GAP-ANALYSIS
├── planning/                   # copies of early Obsidian planning
└── pipeline/                   # ingest / compute / export (May 15+)
```

**Git / remotes:** No production GitHub/Forgejo remote confirmed as of 2026-07-17. Creating `routevault` (or `routevault-staging` → prod) on Forgejo primary + GitHub mirror is a **go-live task**. Prefer Forgejo primary per house convention.

---

## Product snapshot

| Layer | Reality (2026-07-17) |
|-------|----------------------|
| Design / static pages | Strong — full dark SaaS mock set |
| Data | 17 models; 1,530 price rows; **synthetic** 90d history from `init_db.py` |
| Quiz | Data-driven vs `models.json` |
| Model detail | Chart.js price history |
| Benchmarks in DB | **Missing** (only prose / partial sources) |
| Smart router | **Not built** |
| Auth / accounts | Placeholder pages only |
| Public deploy | **Not done** |
| Domain | Target `routevault.ai` — ownership/DNS **unconfirmed in docs** |

**Data honesty:** Price history is a seeded random walk for UI demos, not scraped market truth. Label as demo on v0 or refresh before marketing as intelligence.

`models.json` `generated_at`: **2026-05-14** (stale).

---

## Two visions — locked decision for v0

| Doc | Emphasis |
|-----|----------|
| Business Model / early plan | Tracker + quiz + **router** + SaaS |
| `docs/MVP-Spec.md` (May 15) | **Analytical depth** (price × capability over time); router/auth out of scope |

**v0 ship decision (2026-07-17):** Static analytical/marketing site first (models list, detail, scoring explainer, honest data labels). **No router, no auth, no live proxy** for first public URL. See [[01-Go-Live-Plan]].

---

## Constraints for agents

1. **Edit only under** `/mnt/nas/agents/Projects/RouteVault/` and Obsidian RouteVault folder / kanban.
2. **SQLite on CIFS:** for write-heavy pipeline, copy `data/routevault.db` → local/tmp, write, copy back. Avoid concurrent writers.
3. **Do not invent** production secrets; none required for static v0.
4. **Forgejo = primary**, GitHub = mirror when remotes are created.
5. Scrub credentials before any public push (none expected in this tree today).
6. After material work: update this SoT `last-reviewed`, kanban, and Hermes board (Brief + Ledger + Events) if using Hermes protocol.
7. Prefer **script files** over here-docs; execute and verify, don’t only plan.

---

## Quick verify commands

```bash
# Site files present
ls "/mnt/nas/agents/Projects/RouteVault/code/routevault-staging/"*.html

# DB row counts
sqlite3 "/mnt/nas/agents/Projects/RouteVault/data/routevault.db" \
  "SELECT COUNT(*) FROM models; SELECT COUNT(*) FROM price_history;"

# Local static preview (from any machine with NAS mount)
cd "/mnt/nas/agents/Projects/RouteVault/code/routevault-staging"
python3 -m http.server 8765
# open http://127.0.0.1:8765/
```

---

## Related notes

- [[Project Plan]]
- [[Business Model]]
- [[How do we weight models]]
- [[Competitors]]
- [[01-Go-Live-Plan]]
- [[Kanban/RouteVault]]

---

## Handoff log

| Date | Event |
|------|--------|
| 2026-05-14 | Phase 1 + SQLite seed + quiz data wiring |
| 2026-05-15 | Consolidated under `~/agents/routevault`; analytical MVP spec |
| 2026-07-17 | **All code/data moved to NAS** `/mnt/nas/agents/Projects/RouteVault/`; SoT + Go-Live written; local paths stubbed |

**Next owner action:** Optional: attach `routevault.ai` DNS. Do not start v1b until a billing or Team request lands.
