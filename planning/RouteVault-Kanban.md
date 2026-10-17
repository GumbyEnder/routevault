---
kanban-plugin: board
tags: [routevault, saas, ai-models, planning, mockups, go-live]
status: active
last-reviewed: 2026-08-14
---

## Backlog

- [x] Real price ingest (OpenRouter live) + OpenRouterList weekly history (≤6 months)
- [ ] Benchmark snapshots in DB + UI columns (LMSYS, GPQA, SWE-Bench, etc.)
- [x] User-configurable weighting sliders (Phase 2) — local, Explorer
- [x] Smart route *resolver* (no proxy) + published equivalence floors
- [x] Flesh out harness-detail-hermes with live pairings
- [ ] Attach custom domain routevault.ai when DNS ready
- [ ] **v1b later:** Pro gate, email/Telegram alert delivery, Team seats / SSO / billing

## To Do (User Management v1a — locked; execute this cut)

- [x] v1a: Identity (email + password, session, logout, password-reset API)
- [x] v1a: Replace waitlist login/register with real account pages; nav signed-in vs guest
- [x] v1a: Cloud profile for stack / weights / alerts / resolves (same client shapes)
- [x] v1a: First-login merge (keep local / use cloud / union) — never silent-overwrite
- [x] v1a: Guest path unchanged (localStorage still works with no account)
- [x] v1a: Waitlist email conversion if `routevault.waitlist` matches
- [x] v1a: Hosted user DB (Railway Postgres) — not CIFS SQLite
- [x] v1a: DoD — second-browser sync + automated register/login/logout/unauth/merge tests

## To Do (v0 go-live — execute in order)

- [ ] Phase A: Preview site via `python3 -m http.server` from NAS staging; fix broken paths
- [ ] Phase A: Add demo-data honesty banner on index + models
- [ ] Phase B: Create Forgejo repo (primary) + GitHub mirror; push staging tree
- [ ] Phase C: Deploy static site (Cloudflare Pages preferred) from `code/routevault-staging`
- [ ] Phase D: Record public URL in `00-Source-of-Truth.md`
- [ ] Optional: one-shot refresh of model seed list to current frontier models

## In Progress

## Review

## Done

- [x] **2026-07-17:** Cross-machine handoff package (SoT + Go-Live + NAS code move + local stubs)
- [x] **Phase 1 Static Mockups Complete** — landing, models, model-detail, pricing, quiz, how-we-score, ecosystem, harness placeholder, auth shells
- [x] Dual-layer weighting system defined (Technical + RouteVault Scale)
- [x] Technical metrics table concept + 17–18 model seed
- [x] Interactive onboarding quiz (data-driven vs models.json)
- [x] SQLite DB + 90-day price_history (synthetic seed; 17 models × 90 = 1530 rows)
- [x] Utility scripts: init_db, export_model_data, show_price_history, price_change_report
- [x] Analytical MVP spec + pipeline stubs (May 15)
- [x] **2026-07-17:** All source/data moved to `/mnt/nas/agents/Projects/RouteVault/`; local `~/agents/routevault` and `~/routevault-data` stubbed; vault SoT + Go-Live written

%% kanban:settings
```
{"kanban-plugin":"board","list-collapse":[false,false,false,false,false]}
```
%%
