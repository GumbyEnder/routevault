"""Backfill price history from the public OpenRouterList change-point ledger.

Source: https://github.com/jvrck/openrouterlist  (data/history/prices.json)
Each point is [YYYY-MM-DD, input_usd_per_1M, output_usd_per_1M] recorded when
OpenRouter's listed price changed. We expand those points to a weekly series
inside a lookback window, never inventing prices before first_seen.
"""

from __future__ import annotations

import json
import urllib.request
from datetime import date, datetime, timedelta
from typing import Any, Optional

LEDGER_URL = (
    "https://raw.githubusercontent.com/jvrck/openrouterlist/main/data/history/prices.json"
)
SOURCE = "openrouterlist.jvrck.prices.json"
USER_AGENT = "RouteVault/1.0 (https://routevault-production.up.railway.app)"


def fetch_ledger(timeout: int = 60, dest: Optional[Any] = None) -> dict[str, Any]:
    req = urllib.request.Request(
        LEDGER_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    if dest is not None:
        dest.write_bytes(raw)
    return json.loads(raw.decode("utf-8"))


def load_ledger(path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _as_date(value: str) -> date:
    return datetime.strptime(value[:10], "%Y-%m-%d").date()


def match_record(ledger_models: dict[str, Any], openrouter_id: str, slug: str) -> tuple[Optional[str], Optional[dict[str, Any]]]:
    if openrouter_id in ledger_models:
        return openrouter_id, ledger_models[openrouter_id]
    if slug in ledger_models:
        return slug, ledger_models[slug]
    suffix = "/" + slug
    for key, rec in ledger_models.items():
        if key.endswith(suffix) and ":batch" not in key and ":free" not in key:
            return key, rec
    return None, None


def price_on_or_before(points: list[tuple[date, float, float]], on: date) -> Optional[tuple[float, float]]:
    hit = None
    for d, pin, pout in points:
        if d <= on:
            hit = (pin, pout)
        else:
            break
    return hit


def expand_weekly(
    rec: dict[str, Any],
    *,
    window_start: date,
    window_end: date,
) -> list[tuple[date, float, float]]:
    raw_points: list[tuple[date, float, float]] = []
    for pt in rec.get("points") or []:
        if not isinstance(pt, (list, tuple)) or len(pt) < 3:
            continue
        if pt[1] is None or pt[2] is None:
            continue
        raw_points.append((_as_date(str(pt[0])), float(pt[1]), float(pt[2])))
    raw_points.sort(key=lambda x: x[0])
    if not raw_points:
        return []

    first_seen = _as_date(rec["first_seen"]) if rec.get("first_seen") else raw_points[0][0]
    start = max(window_start, first_seen, raw_points[0][0])
    end = min(window_end, date.today())
    if start > end:
        return []

    wanted: set[date] = set()
    cursor = start
    while cursor <= end:
        wanted.add(cursor)
        cursor += timedelta(days=7)
    wanted.add(end)
    for d, _a, _b in raw_points:
        if start <= d <= end:
            wanted.add(d)

    series: list[tuple[date, float, float]] = []
    for d in sorted(wanted):
        px = price_on_or_before(raw_points, d)
        if px is None:
            continue
        series.append((d, px[0], px[1]))
    return series
