# RouteVault Project Plan

**Status:** Phase 1 Complete + Data Layer Started  
**Last Updated:** 2026-05-14

---

## Overview

RouteVault is a consumer-friendly AI model intelligence platform that helps users find the right model for their needs at the right price. It combines model scoring, pricing tracking, and smart routing.

We are building this in **two clear phases**.

---

## Current Status (May 14, 2026)

### Phase 1 – Static Mockups + Foundation: **Complete**

- All 7 major pages built as high-quality static HTML/JS mockups:
  - Landing, Models, Model Detail, Pricing, Quiz/Onboarding, Dashboard, How We Score
- Technical metrics table populated with 18 models (LMSYS ELO, GPQA, SWE-Bench, latency, tool use)
- Precise consumer-category mapping rules + scoring thresholds defined
- Interactive quiz with smart recommendations implemented (`quiz.html`)
- Dark, premium SaaS design system applied consistently
- Mobile responsiveness improved on key pages (`models.html`, nav, filters)

**Repository:** `github_repos/routevault-staging/`

---

### Data Layer Progress (New)

- SQLite database successfully created and populated:
  - 17 models seeded
  - 1,530 price history records (90 days per model)
  - Located at: `scripts/routevault.db` (in staging repo)
- Utility scripts created:
  - `scripts/show_price_history.py` – view 90-day price history for any model
  - `scripts/price_change_report.py` – 30/60/90-day price change deltas across all models
- Data exported for frontend use:
  - `data/models.json` – full model list + 90-day price history (JSON)
- Real historical pricing now wired into `model-detail.html` (Chart.js loads live data from JSON)

**Note:** Database work was moved to a local `~/routevault-data/` environment to avoid CIFS/NAS file-locking issues.

---

### Approach

The site will remain mostly static for now to maximize SEO value while we establish useful, high-quality content. Real data integration is underway. User accounts, authentication, and a smart router are planned for Phase 2+.

---

## Phase 1: Static Mockup Site (Completed)

**Deliverables Achieved:**
- Full set of static pages with consistent branding
- Clear user flows
- Mobile-responsive improvements
- Interactive onboarding quiz with recommendations

---

## Phase 2: Functional Implementation (In Progress)

**Current Focus Areas:**
- Real historical pricing data integration (partially complete)
- Price change indicators and “Price Intelligence” layer
- User-configurable weighting sliders
- Production repository and deployment pipeline
- Smart router + recommendation engine

---

## Immediate Next Steps

1. Add price change indicators and “Price Intelligence” features across the Models page
2. Implement user-configurable weighting sliders / priority settings
3. Create production GitHub repo + deploy pipeline (`routevault.ai`)
4. Begin work on smart router + recommendation engine

---

## Architecture Notes

- Static-first approach for SEO
- Lightweight SQLite for historical pricing and model data (initially)
- Local database development environment used to avoid NAS locking
- Long-term roadmap includes logins, saved stacks, and a smart router

---

**Next Direction Requested:** All 4 remaining Backlog items (user directive). Work is underway.