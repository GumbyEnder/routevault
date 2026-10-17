"""Find OpenRouter models that are not in the curated catalog."""

from __future__ import annotations

from typing import Any

from pipeline.catalog import is_skipped_variant, provider_name
from pipeline.ingest.openrouter import aa_indexes, per_million


def should_promote(rec: dict[str, Any]) -> bool:
    """Frontier-ish: has an Artificial Analysis index and is not a routing variant."""
    if is_skipped_variant(rec.get("id") or ""):
        return False
    aa = aa_indexes(rec)
    return aa["intelligence"] > 0 or aa["coding"] > 0


def scan_new_models(
    raw: list[dict[str, Any]],
    known_openrouter_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (discovered rows for sqlite, OpenRouter records to ingest)."""
    discovered: list[dict[str, Any]] = []
    promote: list[dict[str, Any]] = []
    seen: set[str] = set()
    for rec in raw:
        mid = rec.get("id") or ""
        if not mid or mid in seen:
            continue
        seen.add(mid)
        if is_skipped_variant(mid):
            continue
        if mid in known_openrouter_ids:
            continue
        aa = aa_indexes(rec)
        pin = per_million(rec.get("pricing"), "prompt")
        pout = per_million(rec.get("pricing"), "completion")
        promote_flag = should_promote(rec)
        discovered.append(
            {
                "openrouter_id": mid,
                "display_name": rec.get("name") or mid,
                "provider": provider_name(mid),
                "intelligence": aa["intelligence"],
                "coding": aa["coding"],
                "input_price": pin,
                "output_price": pout,
                "promoted": 1 if promote_flag else 0,
                "reason": "aa_index" if promote_flag else "seen_no_aa",
            }
        )
        if promote_flag:
            promote.append(rec)
    promote.sort(
        key=lambda m: (
            aa_indexes(m)["intelligence"],
            aa_indexes(m)["coding"],
        ),
        reverse=True,
    )
    return discovered, promote[:40]
