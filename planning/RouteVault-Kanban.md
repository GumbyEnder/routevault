---
kanban-plugin: board
tags: [routevault, saas, ai-models, planning, mockups, go-live]
status: active
last-reviewed: 2026-07-17
---

## Backlog

- [ ] Real price ingest (OpenRouter/providers) replacing synthetic history
- [ ] Benchmark snapshots in DB + UI columns (LMSYS, GPQA, SWE-Bench, etc.)
- [ ] User-configurable weighting sliders (Phase 2)
- [ ] Implement smart router + recommendation engine (post-v0)
- [ ] Flesh out harness-detail-hermes with real data
- [ ] Attach custom domain routevault.ai when DNS ready

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
