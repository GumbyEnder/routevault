#!/usr/bin/env python3
"""Ingest live OpenRouter prices + AA benches, compute trends, export frontend JSON."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.catalog import (  # noqa: E402
    assign_label,
    context_score,
    hermes_fit,
    provider_name,
    resolve_catalog,
    slug,
)
from pipeline.compute import calculate_value_score, generate_value_trends_for_model  # noqa: E402
from pipeline.ingest.openrouter import aa_indexes, fetch_openrouter_models, per_million  # noqa: E402
from pipeline.schema import BenchmarkType, ModelSnapshot  # noqa: E402
from pipeline.discover import scan_new_models  # noqa: E402
from pipeline.store import (  # noqa: E402
    connect,
    counts,
    fetch_benchmarks,
    fetch_discovered,
    fetch_models,
    fetch_news,
    fetch_prices,
    record_run,
    upsert_benchmark,
    upsert_discovered,
    upsert_model,
    upsert_news,
    upsert_price,
)

AA_SOURCE = "openrouter.benchmarks.artificial_analysis"
PRICE_SOURCE = "openrouter.api.v1.models"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RouteVault ingest + export")
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--offline", action="store_true", help="Skip network; recompute from SQLite")
    p.add_argument("--skip-export", action="store_true")
    p.add_argument(
        "--backfill-history",
        action="store_true",
        help="Import up to 6 months of OpenRouterList weekly price history",
    )
    p.add_argument("--history-days", type=int, default=183)
    p.add_argument(
        "--discover",
        action="store_true",
        help="Scan OpenRouter for models not in the curated catalog; auto-promote AA-indexed ones",
    )
    p.add_argument(
        "--news",
        action="store_true",
        help="Ingest AI/tech RSS (politics filtered) into news_items",
    )
    p.add_argument("--news-limit", type=int, default=80)
    return p.parse_args()


def backfill_openrouterlist(conn, root: Path, days: int = 183) -> dict[str, Any]:
    from pipeline.ingest.openrouterlist import (
        SOURCE as HIST_SOURCE,
        expand_weekly,
        fetch_ledger,
        load_ledger,
        match_record,
    )

    cache = root / "data" / "cache" / "openrouterlist-prices.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    try:
        ledger = fetch_ledger(dest=cache)
        fetched = True
    except Exception as exc:  # noqa: BLE001 — fall back to last cache
        if not cache.exists():
            raise
        ledger = load_ledger(cache)
        fetched = False
        print(f"ledger fetch failed ({exc}); using cache {cache}")

    ledger_models = ledger.get("models") or {}
    window_end = date.today()
    window_start = window_end - timedelta(days=days)
    rows_written = 0
    covered = 0
    short = []

    for model in fetch_models(conn):
        key, rec = match_record(ledger_models, model["openrouter_id"], model["model_id"])
        if not rec:
            short.append({"model_id": model["model_id"], "reason": "not_in_ledger"})
            continue
        series = expand_weekly(rec, window_start=window_start, window_end=window_end)
        if not series:
            short.append({"model_id": model["model_id"], "reason": "no_points", "ledger": key})
            continue
        covered += 1
        for d, pin, pout in series:
            if d >= window_end:
                continue  # keep today's live OpenRouter snapshot authoritative
            upsert_price(conn, model["model_id"], d, pin, pout, HIST_SOURCE)
            rows_written += 1

    notes = (
        f"openrouterlist as_of={ledger.get('as_of')} fetched={fetched} "
        f"window={window_start.isoformat()}..{window_end.isoformat()} "
        f"models={covered} rows={rows_written}"
    )
    record_run(conn, datetime.now(timezone.utc).isoformat(), covered, notes)
    conn.commit()
    return {
        "source": HIST_SOURCE,
        "ledger_as_of": ledger.get("as_of"),
        "fetched": fetched,
        "window_days": days,
        "models_covered": covered,
        "rows_written": rows_written,
        "short": short,
    }


def ingest_one(conn, rec: dict[str, Any], today: date, now: str) -> str:
    mid = rec["id"]
    model_id = slug(mid)
    pin = per_million(rec.get("pricing"), "prompt")
    pout = per_million(rec.get("pricing"), "completion")
    ctx = int(rec.get("context_length") or 0)
    context_k = max(1, round(ctx / 1000)) if ctx else 0
    aa = aa_indexes(rec)
    label = assign_label(
        aa["intelligence"], aa["coding"], aa["agentic"], pin + pout, context_k
    )
    desc = (rec.get("description") or "").strip()
    if len(desc) > 420:
        desc = desc[:417] + "..."

    upsert_model(
        conn,
        {
            "model_id": model_id,
            "openrouter_id": mid,
            "display_name": rec.get("name") or model_id,
            "provider": provider_name(mid),
            "context_k": context_k,
            "current_input_price": pin,
            "current_output_price": pout,
            "rv_label": label.value,
            "description": desc,
            "knowledge_cutoff": rec.get("knowledge_cutoff") or "",
            "hermes_fit": hermes_fit(
                aa["intelligence"], aa["coding"], aa["agentic"], context_k
            ),
            "is_deprecated": 0,
            "updated_at": now,
        },
    )
    upsert_price(conn, model_id, today, pin, pout, PRICE_SOURCE)

    mapping = {
        BenchmarkType.REASONING.value: aa["intelligence"],
        BenchmarkType.GENERAL_INTELLIGENCE.value: aa["intelligence"],
        BenchmarkType.CODING.value: aa["coding"],
        BenchmarkType.TOOL_USE.value: aa["agentic"],
        BenchmarkType.CONTEXT.value: context_score(context_k),
    }
    for btype, score in mapping.items():
        if score and score > 0:
            upsert_benchmark(conn, model_id, today, btype, score, AA_SOURCE)
    return model_id


def ingest(conn, today: date, *, discover: bool = False) -> dict[str, Any]:
    raw = fetch_openrouter_models()
    chosen = resolve_catalog(raw)
    now = datetime.now(timezone.utc).isoformat()
    ingested = 0
    promoted = 0
    discovered_n = 0

    known = {m["id"] for m in chosen}
    known.update(r["openrouter_id"] for r in fetch_models(conn) if r.get("openrouter_id"))

    recs = list(chosen)
    if discover:
        found, promote_recs = scan_new_models(raw, known)
        for row in found:
            upsert_discovered(conn, row, now)
            discovered_n += 1
        existing_ids = {m["id"] for m in recs}
        for rec in promote_recs:
            if rec["id"] not in existing_ids:
                recs.append(rec)
                existing_ids.add(rec["id"])
                promoted += 1

    for rec in recs:
        ingest_one(conn, rec, today, now)
        ingested += 1

    record_run(
        conn,
        now,
        ingested,
        f"openrouter catalog={len(raw)} curated={len(chosen)} ingested={ingested} discovered={discovered_n} promoted={promoted}",
    )
    conn.commit()
    return {
        "catalog": len(raw),
        "curated": len(chosen),
        "ingested": ingested,
        "discovered": discovered_n,
        "promoted": promoted,
    }


def ingest_news(conn, generated_at: str, limit: int = 80) -> dict[str, Any]:
    from pipeline.ingest.news import collect_news

    result = collect_news()
    written = 0
    for item in result["items"]:
        upsert_news(conn, item, generated_at)
        written += 1
    conn.commit()
    items = fetch_news(conn, limit=limit)
    return {
        "feeds": result["feeds"],
        "fetched": result["kept"],
        "written": written,
        "stored": len(items),
        "errors": result["errors"],
        "items": items,
    }


def _benches_as_of(rows: list[dict[str, Any]], on: str) -> dict[BenchmarkType, float]:
    """Benches on or before `on`, else the earliest later observation.

    We do not invent scores. We *hold* the nearest known AA snapshot so a
    price-only history can still produce a value series. UI copy must say
    capability is last-known, not a reconstructed bench tape.
    """
    by_type: dict[str, list[tuple[str, float]]] = {}
    for r in rows:
        by_type.setdefault(r["benchmark_type"], []).append((r["date"], float(r["score"])))
    out: dict[BenchmarkType, float] = {}
    for btype, series in by_type.items():
        series.sort()
        chosen = None
        for d, score in series:
            if d <= on:
                chosen = score
            else:
                if chosen is None:
                    chosen = score
                break
        if chosen is None:
            continue
        try:
            out[BenchmarkType(btype)] = chosen
        except ValueError:
            continue
    return out


def build_snapshots(
    models: list[dict[str, Any]],
    prices: dict[str, list[dict[str, Any]]],
    benches: dict[str, list[dict[str, Any]]],
) -> dict[str, list[ModelSnapshot]]:
    by_model: dict[str, list[ModelSnapshot]] = {}
    for m in models:
        mid = m["model_id"]
        snaps: list[ModelSnapshot] = []
        for ph in prices.get(mid, []):
            snap = ModelSnapshot(
                model_id=mid,
                date=date.fromisoformat(ph["date"]),
                input_price=float(ph["input_price"]),
                output_price=float(ph["output_price"]),
                benchmarks=_benches_as_of(benches.get(mid, []), ph["date"]),
            )
            snap.compute_derived()
            snap.value_score = calculate_value_score(snap)
            snaps.append(snap)
        by_model[mid] = snaps
    return by_model


def price_change(history: list[dict[str, Any]], days: int) -> float | None:
    if len(history) < 2:
        return None
    end = history[-1]
    end_date = date.fromisoformat(end["date"])
    target = end_date - timedelta(days=days)
    start = None
    for row in history:
        if date.fromisoformat(row["date"]) >= target:
            start = row
            break
    if start is None or start is end:
        start = history[0]
    if start["date"] == end["date"]:
        return None
    s = float(start["input_price"]) + float(start["output_price"])
    e = float(end["input_price"]) + float(end["output_price"])
    if s == 0:
        return None
    return round(((e - s) / s) * 100, 2)


def monthly_estimate(inp: float, out: float) -> int:
    # ~4M in / 1M out tokens — indie-dev sketch, labeled as estimate in UI
    return max(1, round(inp * 4 + out * 1))


def export_frontend(
    models: list[dict[str, Any]],
    prices: dict[str, list[dict[str, Any]]],
    benches: dict[str, list[dict[str, Any]]],
    snaps: dict[str, list[ModelSnapshot]],
    generated_at: str,
) -> dict[str, Any]:
    explorer = []
    details: dict[str, Any] = {}
    trends_30: list[dict[str, Any]] = []
    trends_60: list[dict[str, Any]] = []
    trends_90: list[dict[str, Any]] = []

    for m in models:
        mid = m["model_id"]
        hist = prices.get(mid, [])
        model_snaps = snaps.get(mid, [])
        latest = max(model_snaps, key=lambda s: s.date) if model_snaps else None
        benches_now = {
            (b.value if hasattr(b, "value") else str(b)): score
            for b, score in (latest.benchmarks.items() if latest else [])
        }
        trends = generate_value_trends_for_model(mid, model_snaps) if model_snaps else []
        tmap = {t.window_days: t for t in trends}
        for t in trends:
            blob = json.loads(t.model_dump_json())
            if t.window_days == 30:
                trends_30.append(blob)
            elif t.window_days == 60:
                trends_60.append(blob)
            elif t.window_days == 90:
                trends_90.append(blob)

        t90 = tmap.get(90) or tmap.get(60) or tmap.get(30)
        delta30 = price_change(hist, 30)
        delta90 = price_change(hist, 90)
        value = latest.value_score if latest and latest.value_score is not None else 0.0
        pin = float(m["current_input_price"] or 0)
        pout = float(m["current_output_price"] or 0)

        row = {
            "model_id": mid,
            "openrouter_id": m.get("openrouter_id") or mid,
            "display_name": m.get("display_name") or mid,
            "provider": m["provider"],
            "rv_label": m.get("rv_label") or "Unknown",
            "context_k": int(m.get("context_k") or 0),
            "input_price": pin,
            "output_price": pout,
            "total_price": round(pin + pout, 6),
            "monthly_est": monthly_estimate(pin, pout),
            "value_score": value,
            "price_change_30d": delta30,
            "price_change_90d": delta90,
            "value_improved": bool(t90.value_improved) if t90 else None,
            "value_change_90d": t90.value_change_score if t90 else None,
            "trend_summary": t90.summary if t90 else "Need more history for a trend.",
            "benchmarks": benches_now,
            "hermes_fit": m.get("hermes_fit") or "Unknown",
            "knowledge_cutoff": m.get("knowledge_cutoff") or "",
        }
        explorer.append(row)

        details[mid] = {
            **row,
            "description": m.get("description") or "",
            "price_history": [
                {
                    "date": h["date"],
                    "input": float(h["input_price"]),
                    "output": float(h["output_price"]),
                    "source": h.get("source") or PRICE_SOURCE,
                }
                for h in hist
            ],
            "benchmark_history": [
                {
                    "date": b["date"],
                    "type": b["benchmark_type"],
                    "score": float(b["score"]),
                    "source": b.get("source") or AA_SOURCE,
                }
                for b in benches.get(mid, [])
            ],
            "trends": [json.loads(t.model_dump_json()) for t in trends],
        }

    explorer.sort(key=lambda r: (-(r["value_score"] or 0), r["total_price"]))

    movers = sorted(
        [r for r in explorer if r.get("value_change_90d") is not None],
        key=lambda r: r["value_change_90d"],
        reverse=True,
    )
    cheaper = sorted(
        [r for r in explorer if r.get("price_change_30d") is not None],
        key=lambda r: r["price_change_30d"],
    )

    by_label: dict[str, list[dict[str, Any]]] = {}
    for r in explorer:
        by_label.setdefault(r["rv_label"], []).append(r)

    dataset = {
        "generated_at": generated_at,
        "as_of": date.today().isoformat(),
        "honesty": {
            "prices": "live",
            "price_source": PRICE_SOURCE,
            "benchmarks": "live" if any(r["benchmarks"] for r in explorer) else "missing",
            "benchmark_source": AA_SOURCE,
            "history": "openrouterlist+live",
            "history_source": "openrouterlist.jvrck.prices.json",
            "history_note": (
                "Weekly OpenRouter list prices from the public OpenRouterList "
                "change-point ledger (jvrck/openrouterlist), forward-filled "
                "after first_seen, plus today's live OpenRouter snapshot. "
                "Models newer than the window only show the weeks they existed. "
                "Not provider-direct invoices and not a synthetic random walk."
            ),
            "banner": (
                "Live OpenRouter list prices + Artificial Analysis indexes. "
                "History is weekly OpenRouter list prices from OpenRouterList "
                "(up to 6 months, or since the model first appeared)."
            ),
        },
        "model_count": len(explorer),
        "models": explorer,
        "details": details,
        "value_trends_30d": trends_30,
        "value_trends_60d": trends_60,
        "value_trends_90d": trends_90,
        "insights": {
            "best_value": explorer[:8],
            "value_improvers": movers[:8],
            "value_regressions": list(reversed(movers[-5:])) if movers else [],
            "price_drops_30d": [r for r in cheaper if (r.get("price_change_30d") or 0) < 0][:8],
            "by_label": {
                label: [
                    {
                        "model_id": r["model_id"],
                        "value_score": r["value_score"],
                        "total_price": r["total_price"],
                    }
                    for r in rows[:6]
                ]
                for label, rows in by_label.items()
            },
        },
        "equivalence": build_equivalence(explorer),
        "harnesses": build_harnesses(explorer),
        "weights_default": {
            "reasoning": 0.32,
            "coding": 0.25,
            "tool_use": 0.18,
            "general_intelligence": 0.15,
            "context": 0.07,
            "speed": 0.03,
        },
        "rubric_version": "2026-08-14",
    }
    return dataset


def build_equivalence(explorer: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cheapest model that still clears each RouteVault Scale tier."""
    # Floors mirror the published RouteVault Scale on /how-we-score exactly.
    floors = {
        "Project Planner": {"agentic": 45, "intelligence": 50},
        "Researcher": {"intelligence": 52},
        "Senior Developer": {"coding": 65},
        "Junior Developer": {"coding": 35},
        "Budget Everyday": {"total_price": 2.5},
    }
    tiers = []
    for label, req in floors.items():
        eligible = []
        for r in explorer:
            b = r.get("benchmarks") or {}
            intel = b.get("reasoning") or b.get("general_intelligence") or 0
            coding = b.get("coding") or 0
            agentic = b.get("tool_use") or 0
            ok = True
            if "intelligence" in req and intel < req["intelligence"]:
                ok = False
            if "coding" in req and coding < req["coding"]:
                ok = False
            if "agentic" in req and agentic < req["agentic"]:
                ok = False
            if "total_price" in req and r["total_price"] >= req["total_price"]:
                ok = False
            if ok:
                eligible.append(r)
        eligible.sort(key=lambda r: (r["total_price"], -(r["value_score"] or 0)))
        pick = eligible[0] if eligible else None
        next_up = eligible[1] if len(eligible) > 1 else None
        tiers.append(
            {
                "tier": label,
                "floors": req,
                "pick": pick["model_id"] if pick else None,
                "pick_openrouter_id": pick["openrouter_id"] if pick else None,
                "pick_price": pick["total_price"] if pick else None,
                "alternate": next_up["model_id"] if next_up else None,
                "eligible_count": len(eligible),
            }
        )
    return tiers


def build_harnesses(explorer: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hermes = [r for r in explorer if r.get("hermes_fit") in ("Recommended", "Strong")]
    hermes.sort(key=lambda r: (-(r["benchmarks"].get("tool_use") or 0), r["total_price"]))
    return [
        {
            "id": "hermes",
            "name": "Hermes",
            "blurb": "Multi-agent orchestrator. Prefers high tool-use + long context.",
            "recommended": hermes[:8],
        },
        {
            "id": "picoclaw",
            "name": "PicoClaw",
            "blurb": "Lightweight local-first harness. Budget Everyday models shine.",
            "recommended": sorted(
                [r for r in explorer if r["rv_label"] == "Budget Everyday"],
                key=lambda r: r["total_price"],
            )[:6],
        },
        {
            "id": "openclaw",
            "name": "OpenClaw",
            "blurb": "Open tool-calling runtime. Senior / Junior Dev labels first.",
            "recommended": [
                r
                for r in explorer
                if r["rv_label"] in ("Senior Developer", "Junior Developer")
            ][:6],
        },
    ]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str))


def main() -> int:
    args = parse_args()
    root: Path = args.root
    db_path = root / "data" / "routevault.db"
    staging = root / "code" / "routevault-staging" / "data"
    today = date.today()
    generated_at = datetime.now(timezone.utc).isoformat()

    conn = connect(db_path)
    ingest_info = {"skipped": True}
    history_info = {"skipped": True}
    news_info = {"skipped": True}
    if not args.offline:
        ingest_info = ingest(conn, today, discover=args.discover)
    if args.backfill_history:
        history_info = backfill_openrouterlist(conn, root, days=args.history_days)
    if args.news:
        news_info = ingest_news(conn, generated_at, limit=args.news_limit)

    models = fetch_models(conn)
    prices = fetch_prices(conn)
    benches = fetch_benchmarks(conn)
    snaps = build_snapshots(models, prices, benches)
    stats = counts(conn)
    discovered_rows = fetch_discovered(conn)
    news_rows = fetch_news(conn, limit=args.news_limit)
    conn.close()

    dataset = export_frontend(models, prices, benches, snaps, generated_at)
    dataset["db_counts"] = stats
    dataset["ingest"] = ingest_info
    dataset["history_backfill"] = history_info
    dataset["news"] = {k: v for k, v in news_info.items() if k != "items"}

    news_payload = {
        "generated_at": generated_at,
        "honesty": {
            "kind": "ai_tech_rss",
            "politics_filtered": True,
            "note": "Headlines from AI/tech feeds. Politics keywords dropped. Not a full-text news product.",
        },
        "count": len(news_rows),
        "items": news_rows,
        "ingest": {k: v for k, v in news_info.items() if k != "items"},
    }
    discovered_payload = {
        "generated_at": generated_at,
        "count": len(discovered_rows),
        "promoted": sum(1 for r in discovered_rows if r.get("promoted")),
        "models": discovered_rows,
    }

    if not args.skip_export:
        write_json(root / "data" / "models.json", dataset)
        write_json(root / "data" / "analytical_dataset.json", dataset)
        write_json(staging / "dataset.json", dataset)
        write_json(root / "data" / "news.json", news_payload)
        write_json(staging / "news.json", news_payload)
        write_json(root / "data" / "discovered_models.json", discovered_payload)
        write_json(staging / "discovered_models.json", discovered_payload)
        # Compact list used by older quiz path
        write_json(
            staging / "models.json",
            {
                "generated_at": generated_at,
                "models": [
                    {
                        "model_id": m["model_id"],
                        "provider": m["provider"],
                        "context_k": m["context_k"],
                        "current_input_price": m["input_price"],
                        "current_output_price": m["output_price"],
                        "rv_label": m["rv_label"],
                        "price_history": dataset["details"][m["model_id"]]["price_history"],
                    }
                    for m in dataset["models"]
                ],
            },
        )

    print(f"models={stats['models']} prices={stats['price_history']} benches={stats['benchmark_history']} news={stats.get('news_items', 0)} discovered={stats.get('discovered_models', 0)}")
    print(f"ingest={ingest_info}")
    print(f"news={ {k: v for k, v in news_info.items() if k != 'items'} }")
    print(f"wrote {staging / 'dataset.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
