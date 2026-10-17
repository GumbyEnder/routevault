# RouteVault — complete browser test prompt (hand this to another agent)

Copy everything below the line.

---

You are a QA agent. Your job is to **fully test the live RouteVault product in a real browser**, not just curl. Do not implement features unless a test is blocked by a clear bug you can fix in the canonical tree.

## Product

RouteVault is a consumer AI-model intelligence site: live OpenRouter list prices + Artificial Analysis indexes, RouteVault Scale labels, explorer, trends, quiz, local My Stack, and a **route resolver** (not a token proxy).

**Live URL:** https://routevault-production.up.railway.app  
**Canonical code:** `/mnt/nas/agents/Projects/RouteVault/code/routevault-staging/`  
**Dataset:** `/data/dataset.json` on the live host (must be HTTP 200, `honesty.prices === "live"`).  
**Railway:** project `routevault` `37267b3e-5395-431d-beda-f1982c9fb32c`, service `routevault`, env `production`.  
**Do not use:** `~/agents/routevault`, Cloudflare tunnel URLs, or `/mnt/nas/github_repos/routevault-staging`.

NAS must be mounted if you edit. If `/mnt/nas` is missing, stop and report.

## How to test

Use a real browser (Playwright, Puppeteer, or Chrome DevTools). **A single screenshot is not enough.** Click, type, navigate, and check state across pages.

1. Desktop viewport (~1280×900) **and** mobile (~390×844).
2. Visit every route below.
3. Hunt regressions: empty states, missing JSON, broken nav, stale mock copy.
4. After any fix, re-verify the failed flow and two neighboring pages.

## Routes (all must 200)

`/`, `/models.html`, `/model-detail.html?id=<a real model_id from dataset>`, `/trends.html`, `/route.html`, `/quiz.html`, `/stack.html`, `/how-we-score.html`, `/ecosystem.html`, `/harness-detail-hermes.html`, `/pricing.html`, `/login.html`, `/register.html`, `/account.html`, `/merge.html`, `/reset.html`, `/admin-dashboard.html`, `/assets/rv.js`, `/assets/rv.css`, `/data/dataset.json`, `/api/health`.

## Contract checks (fail the test if any break)

- Banner text is the **live** honesty line (OpenRouter + Artificial Analysis, history is ingest-accumulated). It must **not** say prices are synthetic / demo random-walk.
- Home shows **30** (or whatever `dataset.model_count` is) models tracked, not “187 models”.
- Explorer table is filled from `dataset.json`, not the old hardcoded grok-4 / claude-4-opus mock list.
- Every listed model has an `openrouter_id` containing `/`.
- 30-day Δ may be “—” on day-one history. That is **pass**, not fail. Inventing a 90-day tape is a fail.
- Login/register must **not** pretend a real auth backend exists.

## Browser scenarios (do each)

### A. Home
- Banner loaded (not “Loading live catalog…” stuck).
- Stat cards: model count, best-value id, cheapest id.
- Equivalence cards render; “Route this” on Researcher goes to `/route.html?tier=Researcher` and auto-resolves.

### B. Explorer (`/models.html`)
- Table has ~30 rows; first row is a real slug (e.g. `deepseek-v4-flash-0731` at time of ship).
- Search “claude” filters to Anthropic rows.
- Label chip / select “Budget Everyday” hides Project Planner rows.
- Move the Reasoning slider; **Value** column numbers change.
- Reset weights restores defaults.
- “Hermes recommended” filter leaves only Recommended.
- Click **Open** on a row → detail for that id.
- Click **Stack** → toast; badge on nav increments.

### C. Model detail
- Open `/model-detail.html?id=claude-opus-5` (or current opus slug if renamed).
- Header, prices, AA benches, price chart (one point is OK), radar, peers in same label.
- **Add to My Stack** then go to `/stack.html` and see it listed.
- **Route cheaper** pre-fills `current=` and resolves.

### D. Trends
- Scale buckets list real models.
- Improvers / 30d drops may be empty with an honest empty state. Fail if the page shows fake movers.

### E. Quiz
- Answer all 4 questions (try two paths: cheap+chat vs premium+planning).
- Results are 3 live model ids + a planner/daily pair.
- **Save** and **Save pair** write to `localStorage` key `routevault.stack.v1`.
- Retake works.

### F. My Stack + alerts
- Empty state if you clear `localStorage`.
- With stacked models: remove one; count drops.
- Add an alert rule; it persists in `routevault.alerts.v1`.
- Would-have-saved card shows a dollar sketch (may be $0 if already on the cheapest equivalent).

### G. Route resolver
- Pick **Project Planner** vs current `claude-opus-5`.
- Must show Resolved + an OpenRouter id + JSON ledger (`proxy: false`).
- Copy id works (clipboard may need permission — note if blocked).
- Confirm `localStorage.routevault.routes.v1` appended.
- Repeat Budget Everyday; pick should be a cheap model (was `openai/gpt-oss-120b` at ship).

### H. Scoring / harnesses / pricing
- How we score lists rubric v2026-08-14 and live label counts.
- Ecosystem + Hermes detail tables use live pairings, not “12,400 users”.
- Pricing: Free / $19 / $49; waitlist pages do not submit to a backend.

### I. Mobile
- Nav usable (links may hide; brand + CTAs must work).
- Explorer horizontal scroll doesn’t clip the Open button.
- Quiz options tappable.

### J. Resilience
- Throttle offline after first load: pages that already have JS may still run; hard-reload of `/models.html` should not show the old mock table.
- `dataset.json` `honesty.prices` stays `"live"`.

## Out of scope (do not file as bugs)

- No custom domain `routevault.ai` yet.
- No token proxy / BYOK network calls.
- No email/Telegram alert delivery.
- No multi-week price tape until a second ingest (`scripts/refresh.sh`).
- v1a accounts are live. Login/register must create a real session (`/api/health` reports `accounts: true`). Guest localStorage still works. Do not expect Pro billing, email alerts, or emailed reset tokens.

## Report format

```
PASS/FAIL per scenario A–J
Bugs (severity, url, repro, expected, actual)
localStorage keys observed
dataset.generated_at / as_of / model_count
Whether you used desktop + mobile
Blocked: yes/no + reason
```

If you find a real bug in the static site, fix only under  
`/mnt/nas/agents/Projects/RouteVault/code/routevault-staging/`  
then `cd` there and `railway up --detach -m "fix: …"` and re-test the failed scenario. Do not rebuild the router or rewrite the stack.

---
