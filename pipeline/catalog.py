"""Curated frontier catalog + RouteVault Scale labeling."""

from __future__ import annotations

from typing import Any, Optional

from .schema import RouteVaultLabel

# Preferred OpenRouter ids. If an id vanishes, resolve() falls back by prefix.
CURATED_IDS: list[str] = [
    "anthropic/claude-opus-5",
    "anthropic/claude-sonnet-5",
    "anthropic/claude-haiku-4.5",
    "openai/gpt-5.6-sol",
    "openai/gpt-5.6-terra",
    "openai/gpt-5.6-luna",
    "openai/gpt-5.4-mini",
    "openai/gpt-oss-120b",
    "google/gemini-3.7-flash",
    "google/gemini-3.1-pro-preview",
    "google/gemini-3.5-flash-lite",
    "google/gemma-4-31b-it",
    "x-ai/grok-4.6",
    "x-ai/grok-build-0.1",
    "deepseek/deepseek-v4-pro-0813",
    "deepseek/deepseek-v4-flash-0731",
    "meta-llama/llama-4-maverick",
    "meta-llama/llama-3.3-70b-instruct",
    "mistralai/mistral-medium-3-5",
    "mistralai/mistral-small-2603",
    "qwen/qwen3.8-max",
    "qwen/qwen3.7-plus",
    "qwen/qwen3-coder-next",
    "moonshotai/kimi-k3",
    "moonshotai/kimi-k2.6",
    "z-ai/glm-5.2",
    "z-ai/glm-4.7",
    "minimax/minimax-m3",
    "nousresearch/hermes-4-70b",
    "cohere/command-a",
]

SKIP_SUFFIXES = (
    ":free",
    ":batch",
    ":nitro",
    ":extended",
    ":online",
    ":floor",
    ":exacto",
)

PROVIDER_NAMES = {
    "anthropic": "Anthropic",
    "openai": "OpenAI",
    "google": "Google",
    "x-ai": "xAI",
    "deepseek": "DeepSeek",
    "meta-llama": "Meta",
    "mistralai": "Mistral",
    "qwen": "Alibaba",
    "moonshotai": "Moonshot",
    "z-ai": "Zhipu",
    "minimax": "MiniMax",
    "nousresearch": "Nous Research",
    "cohere": "Cohere",
    "amazon": "Amazon",
}


def slug(openrouter_id: str) -> str:
    return openrouter_id.split("/", 1)[-1]


def provider_name(openrouter_id: str) -> str:
    org = openrouter_id.split("/", 1)[0]
    return PROVIDER_NAMES.get(org, org.replace("-", " ").title())


def is_skipped_variant(model_id: str) -> bool:
    low = model_id.lower()
    return any(s in low for s in SKIP_SUFFIXES)


def resolve_catalog(openrouter_models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return one live OpenRouter record per curated id (or best prefix fallback)."""
    by_id = {m["id"]: m for m in openrouter_models if not is_skipped_variant(m["id"])}
    chosen: list[dict[str, Any]] = []
    seen: set[str] = set()

    for wanted in CURATED_IDS:
        rec = by_id.get(wanted)
        if rec is None:
            prefix = wanted
            candidates = [
                m
                for mid, m in by_id.items()
                if mid.startswith(prefix) or mid.startswith(wanted.rsplit("-", 1)[0])
            ]
            rec = _best_candidate(candidates)
        if rec is None or rec["id"] in seen:
            continue
        seen.add(rec["id"])
        chosen.append(rec)
    return chosen


def _best_candidate(rows: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not rows:
        return None

    def key(m: dict[str, Any]) -> tuple:
        aa = ((m.get("benchmarks") or {}).get("artificial_analysis") or {})
        intel = float(aa.get("intelligence_index") or 0)
        coding = float(aa.get("coding_index") or 0)
        return (intel, coding, m.get("context_length") or 0)

    return max(rows, key=key)


def assign_label(
    intelligence: float,
    coding: float,
    agentic: float,
    total_price: float,
    context_k: int,
) -> RouteVaultLabel:
    """Map technical scores + price into the RouteVault Scale.

    Mirrors the published table on /how-we-score:
      Project Planner — agentic >= 45 and intelligence >= 50
      Researcher — intelligence >= 52, or >= 45 with >= 400k context
      Senior Developer — coding >= 65 (or >= 50 if not cheap)
      Junior Developer — coding >= 35
      Budget Everyday — combined list price under $2.50/M
      Specialist — thin bench coverage or narrow models
    """
    if agentic >= 45 and intelligence >= 50:
        return RouteVaultLabel.PROJECT_PLANNER
    if intelligence >= 52:
        return RouteVaultLabel.RESEARCHER
    if intelligence >= 45 and context_k >= 400:
        return RouteVaultLabel.RESEARCHER
    # coding >= 65 is Senior at any price ("or >= 50 if not cheap" is the
    # discount path, never a demotion path for strong coders).
    if coding >= 65:
        return RouteVaultLabel.SENIOR_DEV
    if coding >= 50:
        return RouteVaultLabel.SENIOR_DEV if total_price >= 3 else RouteVaultLabel.JUNIOR_DEV
    if coding >= 35:
        return RouteVaultLabel.JUNIOR_DEV
    # Leftover generalists: Budget only when actually cheap. Expensive models
    # without a coding index are Specialists, not Budget.
    if total_price < 2.5:
        return RouteVaultLabel.BUDGET_EVERYDAY
    return RouteVaultLabel.SPECIALIST


def hermes_fit(intelligence: float, coding: float, agentic: float, context_k: int) -> str:
    """How well this model pairs with the Hermes harness."""
    if agentic >= 45 and intelligence >= 50 and context_k >= 128:
        return "Recommended"
    if agentic >= 30 and coding >= 40:
        return "Strong"
    if intelligence >= 25:
        return "Usable"
    return "Limited"


def context_score(context_k: int) -> float:
    if context_k <= 0:
        return 0.0
    # 16k → ~20, 128k → ~55, 200k → ~65, 1M → 100
    return round(min(100.0, max(8.0, (context_k ** 0.5) * 3.15)), 1)
