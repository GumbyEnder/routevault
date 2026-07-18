# RouteVault Data Model — Deeper Analytical MVP

**Last updated:** 2026-05-15

This document explains the data model used for the deeper, more analytical version of RouteVault.

## Philosophy

The goal is to move beyond "current price + current benchmarks" and instead track **how models change in value over time**.

This requires a time-series approach with snapshots.

---

## Core Concepts

### 1. Model
Represents a specific model (e.g. `claude-3.7-sonnet`, `gpt-4o`, `deepseek-v3`).

Contains relatively stable information:
- Provider
- RouteVault Label (`Researcher`, `Project Planner`, `Budget Everyday`, etc.)
- Context window size
- Current pricing (latest known)

### 2. PriceSnapshot
A price record for a model at a specific date.

Fields:
- `model_id`
- `date`
- `input_price`
- `output_price`

We keep historical price data so we can calculate 30/60/90-day changes and volatility.

### 3. BenchmarkSnapshot
A benchmark score for a model at a specific date.

We support multiple benchmark types:
- `reasoning`
- `coding`
- `tool_use`
- `general_intelligence`
- `context`
- `speed`

This allows us to track how capabilities move alongside price.

### 4. ModelSnapshot (Most Important)
A **point-in-time view** of a model.

It combines:
- Pricing at that date
- All available benchmark scores at that date
- Computed fields (value score, price/performance ratio)

This is the atomic unit we use for trend analysis.

### 5. ValueTrend
Represents how a model's value changed over a time window (30, 60, or 90 days).

Contains:
- Price change %
- Movement in key benchmarks
- Overall "value improved?" flag
- Human-readable summary

This is one of the highest-leverage outputs of the system.

---

## Analytical Flow

1. We maintain historical `PriceSnapshot`s and `BenchmarkSnapshot`s.
2. We periodically create `ModelSnapshot`s (daily or weekly).
3. The compute engine compares snapshots across time windows to produce `ValueTrend`s.
4. These trends power the Models Explorer, Model Detail page, and Trends Dashboard.

---

## Future Considerations

- Support for multiple "as of" dates per month
- Provenance tracking (where each benchmark score came from)
- User-defined weighting profiles
- Ability to run "what if" scenarios on historical data

---

This model is intentionally designed to support deep analysis rather than just current-state comparison.