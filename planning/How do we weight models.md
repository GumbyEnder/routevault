# How Do We Weight Models?

**Project:** RouteVault  
**Goal:** Create a transparent, dual-layer weighting system that powers both accurate technical comparisons and consumer-friendly recommendations.

---

## 1. Overview

We will maintain **two parallel weighting systems**:

1. **Traditional Technical Layer** — Objective, data-driven scores pulled from public benchmarks.
2. **Consumer-Friendly Layer (RouteVault Scale)** — Human-readable categories that normal people actually understand and care about.

The technical layer feeds the consumer layer. Users will primarily see the consumer-friendly labels, with the option to drill into the raw technical data.

---

## 2. Traditional Technical Weighting System

### Core Metrics We Will Track
- **Context Window** (total tokens)
- **Tool Use / Function Calling** quality & reliability
- **Reasoning & Planning** (multi-step, agentic performance)
- **Coding Performance** (small vs complex/repo-scale)
- **Vision / Multimodal** capability
- **Speed** (tokens/sec + time-to-first-token)
- **Price** (input + output per 1M tokens)
- **Instruction Following & Coherence**
- **Knowledge Cutoff** & recency

### Normalization Approach
All metrics will be normalized to a **0–100 scale** so they can be combined and compared.

### Primary Data Sources
| Metric                    | Primary Sources                                      | Notes |
|---------------------------|------------------------------------------------------|-------|
| Context Window            | Provider docs + Artificial Analysis                  | Always use official numbers |
| Tool Use                  | Artificial Analysis + LMSYS Arena + provider tests   | - |
| Reasoning & Planning      | GPQA, HLE, Big-Bench Hard, Agentic benchmarks        | - |
| Coding Performance        | SWE-Bench, LiveCodeBench, HumanEval, Aider          | Split small vs complex |
| Speed & Latency           | Artificial Analysis + Artificial Analysis            | - |
| Price                     | Provider pricing pages + OpenRouter catalog          | Update weekly |
| Overall Intelligence      | LMSYS Chatbot Arena + Artificial Analysis            | - |

---

## 3. Consumer-Friendly Weighting System (The RouteVault Scale)

Instead of showing raw numbers, we will map models into clear, relatable categories:

### Primary Consumer Categories
- **Researcher / Deep Thinker**  
  Best for long-form analysis, complex reasoning, and multi-step research.
- **Project Planner / Agentic**  
  Strong at breaking down goals, using tools, and executing real projects.
- **Senior Developer**  
  Handles architecture, large codebases, and complex technical decisions.
- **Junior Developer / Small Code**  
  Fast, cheap, and reliable for scripts, bug fixes, and daily coding tasks.
- **Creative Writer**  
  Excellent at tone, storytelling, and long-form creative work.
- **Budget Everyday**  
  Good enough for quick answers, chat, and high-volume use at low cost.
- **Specialist** (Vision, Math, Code-only, etc.)

### Weighting Rules (Draft)
- High reasoning + long context + tool use → Researcher / Project Planner
- Strong coding benchmarks + speed → Senior or Junior Developer
- Low price + decent performance → Budget Everyday
- Excellent creative benchmarks → Creative Writer

Users will be able to adjust priorities (e.g., “I care more about price than peak intelligence”).

---

## 4. Data Collection & Maintenance Plan

- **Weekly automated pull** of pricing and basic specs
- **Monthly manual review** of new benchmark releases
- **Source of truth**: A structured table (CSV + Obsidian table) with columns for every metric + source link
- **Versioning**: Every major update will be logged with date and source

---

## 5. Implementation Roadmap

1. **Phase 1** — Build the technical data table with current top 20–30 models
2. **Phase 2** — Define and test the consumer category mapping rules
3. **Phase 3** — Add user-configurable weighting sliders
4. **Phase 4** — Integrate into the RouteVault product (tracker + router)

---

**Next Action:**  
Would you like me to start populating the technical metrics table with real data and sources for the top models? Or shall we first refine the consumer category definitions?