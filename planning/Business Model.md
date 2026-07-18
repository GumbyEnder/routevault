# BestRoute Business Model

**Temporary Project Name:** BestRoute (AI Consumer Intelligence)

## Value Proposition
Up-to-date intelligence for the AI consumer/geek: frontier models, pricing, harnesses (Hermes, PicoClaw, OpenClaw, etc.), and other tools.

- Free tracker with plain-English use-case scoring (deep planning vs small code vs budget chat).
- Smart router that auto-switches to best-price equivalents.
- Real savings and harness/tool recommendations every month for indie devs, hobbyists, and small teams.

## Target Customers
- Primary: Indie hackers, solo developers, small teams, hobbyists building with LLMs and AI tools.
- Secondary: Power users who already spend $50–200+/mo on OpenRouter, Anthropic, OpenAI, etc.
- Pain: Price opacity, surprise bills, manual comparison fatigue, overpaying for capability they don’t need, missing the best harnesses/tools.

## Revenue Streams
1. **Platform Fee (Core)**: 3–5% on all routed token volume (OpenRouter-style, zero markup on base model prices). Users still save money.
2. **Freemium Tiers**:
   - **Free**: Basic tracker access + price-based switching on OpenRouter only. Generous monthly token limit (e.g., 500k–1M).
   - **Pro ($9–19/mo)**: Advanced rules (quality threshold + savings %), multi-provider support, analytics dashboard, saved stacks, priority alerts, zero extra latency.
   - **Team ($29–49/mo)**: Team seats, shared rules, audit logs, volume discounts, SSO.
3. **Affiliate/Partnerships** (optional): Small credits or revenue share when users sign up for OpenRouter or other providers via us.

## Unit Economics (Conservative)
- Average indie user spend: $50–200/mo.
- Our take: $2–10 per active user/mo (after platform fee).
- Break-even: ~100–300 active users (very achievable via Product Hunt + Reddit + X).
- $10k MRR target: 1k–5k users or a few high-volume teams.
- Infra cost at launch: <$50/mo (Fly.io/Railway + Supabase + Upstash Redis).
- At 1k users: Still <$200–500/mo infra → healthy margins.

## Go-to-Market Strategy
- **Free front door**: Mobile-first PWA tracker with quiz → instant personalized recommendations → one-click "Route this".
- Viral hooks: Shareable savings reports ("I saved $47 last month"), before/after stories on Reddit (r/LocalLLaMA, r/SideProject), Product Hunt launch.
- Content: "Best models for indie hackers 2026", "Stop overpaying for Claude", use-case explainers.
- Bootstrap: Generous free tier + lifetime discount for early users. Seed with affiliate OpenRouter signups.
- Retention: Weekly personalized digests ("Your models changed — here’s the impact"), usage-based alerts.

## Differentiation
- Consumer storytelling vs pure tables (PricePerToken, BenchLM).
- Auto best-price switching vs manual or reliability-only routers (LiteLLM, Portkey).
- Same scoring engine powers both tracker and router → seamless funnel.
- Coverage of harnesses/tools (Hermes, PicoClaw, OpenClaw) as core intelligence, not just models.

## Risks & Mitigations
- **Adoption**: Low if no savings proof. Mitigate with real user savings stories + generous free tier.
- **Equivalence mapping**: Hard to define "good enough". Mitigate with community-voted tiers + user overrides.
- **Latency**: Extra hop. Mitigate with edge deployment (Fly.io) and "zero latency mode" on paid plans.
- **Competition**: LiteLLM + OpenRouter. Win on simplicity + consumer UX.
- **Trust**: Users wary of proxy. Mitigate with BYOK (bring your own key) and open-source core.

## Next Steps (Business)
1. Finalize pricing tiers and free limits.
2. Define exact equivalence scoring rules (technical side).
3. Create landing page wireframe + value prop copy.
4. Build MVP tracker first (drives acquisition).
5. Launch on Product Hunt with savings calculator demo.

**Status**: Business model drafted and owned. Ready to refine or move to technical project plan.