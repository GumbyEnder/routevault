# RouteVault — Deeper Analytical MVP Specification

**Project:** RouteVault  
**Version:** Deeper Analytical MVP  
**Date:** 2026-05-15  
**Status:** In Progress  
**Owner:** Grok (with GumbyEnder)

---

## 1. Vision & Goal

**Core Thesis:**

RouteVault should become a high-signal research and analysis tool that helps serious AI tinkerers understand **how the price and real capability of models have moved together over time**.

The product’s primary value is **depth of insight**, not breadth of features or beautiful marketing pages.

**Target User:**
Power users and AI tinkerers who actively manage multiple models, care about cost optimization, and want to make data-informed decisions about which models to use for different types of work.

---

## 2. MVP Success Criteria

By the end of this MVP, a user should be able to:

- See which models have become meaningfully better (or worse) value over the last 30/60/90 days when combining price and performance.
- Understand price trends in the context of actual benchmark movement.
- Filter and analyze models by category (using the RouteVault Scale) and value trends.
- Get non-trivial analytical insights they cannot easily get from OpenRouter, Artificial Analysis, or LiteLLM today.

**Success Metric (Qualitative):**
An experienced AI tinkerer should say: “This is actually useful for understanding the market over time.”

---

## 3. Core Principles for This MVP

- **Depth over Polish**: Better to have powerful analysis with a rougher UI than a beautiful but shallow product.
- **Price + Performance Together**: Price history without benchmarks is weak. Benchmarks without price context are also weak.
- **Historical Analysis is First-Class**: The ability to see movement over time is the main differentiator.
- **Keep Scope Tight**: We will ruthlessly cut anything that does not contribute to analytical depth in the first version.
- **Data is the Product**: The quality and structure of the data layer will determine the ceiling of the tool.

---

## 4. In Scope for MVP

### 4.1 Core Experiences

| Feature | Priority | Description |
|--------|----------|-----------|
| **Models Explorer** | P0 | Main analytical table with price trends + key benchmarks + derived value metrics |
| **Model Detail + Trend Analysis** | P0 | Deep view of one model showing price movement correlated with benchmark movement |
| **Value Trends Dashboard** | P1 | High-level insights (biggest value movers, category trends) |
| **Weighting / Lens Controls** | P1 | Basic ability to emphasize different factors (Price vs Reasoning vs Coding etc.) |
| **Improved Data Pipeline** | P0 | Clean, maintainable way to ingest and store historical price + benchmark data |

### 4.2 Benchmarks (Initial Set)

We will support these core benchmarks in the MVP:

- **Reasoning & Planning** (Highest priority)
- **Coding Performance**
- **Tool Use / Function Calling**
- **General Intelligence** (Arena-style or composite)
- **Context Handling**
- **Speed / Latency** (lighter treatment)

### 4.3 Time Windows

The system should support analysis across at least:
- 30 days
- 60 days
- 90 days

With the ability to compare current state vs past state.

---

## 5. Out of Scope for MVP

- Quiz / Recommendation engine (secondary)
- User accounts & authentication *(analytical MVP out; product cut is now `USER-MANAGEMENT-V1A.md`)*
- Saved stacks / personal dashboards *(local stacks shipped in v0.2; cloud sync is v1a)*
- Actual model routing / proxying
- Hermes-specific features (data should be usable by Hermes, but no deep integration yet)
- Export functionality
- Most marketing pages (`pricing.html`, `ecosystem.html`, etc.)
- Team features
- Alerts / notifications

---

## 6. Data Model (Proposed)

We need a schema that supports historical snapshots.

### Core Entities

**Models**
- `model_id`
- `provider`
- `rv_label` (RouteVault Scale category)
- `context_k`
- Current pricing fields

**Price Snapshots**
- `model_id`
- `date`
- `input_price`
- `output_price`

**Benchmark Snapshots**
- `model_id`
- `date`
- `benchmark_name`
- `score`
- `source`

**Derived Metrics** (can be computed or stored)
- Price change % over N days
- Value Score (composite of price + selected benchmarks)
- Value Trend (change in Value Score over time)

---

## 7. Key Views (High Level)

### 7.1 Models Explorer (Main Screen)
- Filterable, sortable table
- Columns should include:
  - Model + Provider + rv_label
  - Current price
  - Price change (30/60/90d)
  - Selected benchmark scores
  - Value Score
  - Value Trend (30/60/90d)
- Strong filtering on categories and value movement

### 7.2 Model Intelligence Page
- Price history chart
- Benchmark trend lines
- Explicit analysis text (e.g. “Price dropped 19% while Reasoning score improved 6%”)
- Peer comparison

### 7.3 Trends Dashboard
- Top 10 models by value improvement (last 30/60/90 days)
- Category-level movement
- Notable regressions

---

## 8. Technical Approach (Recommended)

**Short term (MVP):**
- Keep the site as a **static HTML + JavaScript** frontend (for speed and SEO).
- Use a strong Python data pipeline to generate rich JSON datasets.
- The frontend consumes pre-computed analytical JSON files.

**Longer term:**
- We can evolve toward a lightweight backend if the analytical needs grow too complex for static generation.

**Data Pipeline Responsibilities:**
- Ingest new price data
- Ingest benchmark data (manual + automated where possible)
- Compute derived metrics (value scores, trends)
- Export clean, queryable JSON for the frontend

---

## 9. Phased Build Order (Recommended)

**Phase 0 – Foundation**
- Finalize data model
- Build improved data pipeline
- Create historical snapshot capability

**Phase 1 – Core Analytical Experience**
- Build the Models Explorer with value trends
- Build the Model Detail + Trend Analysis page

**Phase 2 – Insights Layer**
- Build the Trends Dashboard
- Add basic weighting controls

**Phase 3 – Polish & Validation**
- Improve UX of the explorer
- Add explanations and help text
- Internal testing with real usage

---

## 10. Open Questions

- How will we source and maintain historical benchmark data?
- What level of automation do we want for the data pipeline in the MVP?
- Should we support multiple “snapshots” per month or just monthly snapshots?
- Do we want to allow users to create custom categories or weightings in the MVP?

---

## 11. Next Actions

1. Finalize benchmark list and data sources
2. Design the detailed data schema
3. Begin implementation of the data pipeline
4. Start building the Models Explorer

---

*This document is the source of truth for the Deeper Analytical MVP. It should be updated as decisions are made.*