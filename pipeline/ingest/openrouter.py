"""Fetch live OpenRouter catalog (prices + Artificial Analysis indexes)."""

from __future__ import annotations

import json
import urllib.request
from typing import Any

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
USER_AGENT = "RouteVault/1.0 (https://routevault-production.up.railway.app)"


def fetch_openrouter_models(timeout: int = 45) -> list[dict[str, Any]]:
    req = urllib.request.Request(
        OPENROUTER_MODELS_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return list(payload.get("data") or [])


def per_million(pricing: dict[str, Any] | None, key: str) -> float:
    if not pricing:
        return 0.0
    raw = pricing.get(key)
    if raw is None or raw == "":
        return 0.0
    try:
        return round(float(raw) * 1_000_000, 6)
    except (TypeError, ValueError):
        return 0.0


def aa_indexes(model: dict[str, Any]) -> dict[str, float]:
    benches = model.get("benchmarks") or {}
    aa = benches.get("artificial_analysis") or {}
    return {
        "intelligence": _num(aa.get("intelligence_index")),
        "coding": _num(aa.get("coding_index")),
        "agentic": _num(aa.get("agentic_index")),
    }


def _num(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
