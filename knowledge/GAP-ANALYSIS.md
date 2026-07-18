# RouteVault — Gap Analysis

**Date:** 2026-05-14

## Major Gaps Between Vision and Implementation

### 1. Intelligence Layer (Biggest Gap)

**Vision:**
- Dual-layer scoring system (Technical benchmarks + Consumer-friendly RouteVault Scale)
- Models intelligently matched to user needs via quiz + sliders
- "Price Intelligence" as a core differentiator

**Reality:**
- Only the Quiz has started using real data (as of May 2026)
- No user-configurable weighting exists
- Price change indicators and intelligence are almost non-existent in the UI
- Technical benchmarks (LMSYS, GPQA, SWE-Bench, tool use, etc.) are not exposed

**Impact:** High — This is the core value proposition of the project.

### 2. Price Intelligence

**Vision:**
- Historical pricing + change detection
- "This model dropped 22% last month" type signals
- Helps users make cost-conscious decisions

**Reality:**
- Price history is stored and visible only on `model-detail.html`
- No indicators on the main Models list
- No "Price Intelligence" section or alerts anywhere

**Impact:** High — One of the clearest differentiators vs competitors.

### 3. Hermes / Harness Integration

**Vision:**
- Harnesses (especially Hermes) are first-class citizens in the intelligence layer
- Users can see which models work best with powerful agentic harnesses

**Reality:**
- `harness-detail-hermes.html` exists but is very thin/placeholder
- No real data connection between RouteVault models and Hermes capabilities

**Impact:** Medium-High (strategic for the broader ecosystem)

### 4. Production & Distribution

**Vision:**
- Public site at `routevault.ai`
- Real usage, SEO value, feedback loop

**Reality:**
- Still lives entirely in `routevault-staging`
- No deployment pipeline yet

**Impact:** Medium (blocks real validation and momentum)

---

## Summary of Gap Severity

| Area | Gap Size | Urgency |
|------|----------|---------|
| Intelligence & Scoring | Large | Very High |
| Price Intelligence UI | Large | High |
| User Control (weighting sliders) | Large | High |
| Harness Integration | Medium-Large | Medium |
| Production Deployment | Medium | Medium |

---

## Positive Notes

- The visual foundation is genuinely excellent.
- The data layer (DB + export) is solid and well thought out.
- The Quiz improvements in May 2026 show the right direction.
- Planning documentation in Obsidian is high quality.

The project has a **strong skeleton** — it now needs **real muscle** in the intelligence and data presentation layers.