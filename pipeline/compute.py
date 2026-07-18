"""
RouteVault - Analytical Compute Engine

This module contains the core logic for calculating value scores,
price/performance trends, and derived insights.

This is the heart of the "Deeper Analytical" version of RouteVault.
"""

from datetime import date, timedelta
from typing import List, Dict, Optional
from .schema import (
    ModelSnapshot,
    ValueTrend,
    BenchmarkType,
    RouteVaultLabel,
)


def calculate_value_score(
    snapshot: ModelSnapshot,
    weights: Optional[Dict[BenchmarkType, float]] = None
) -> float:
    """
    Calculate a composite value score for a model snapshot.

    Higher score = better value (higher performance relative to price).

    Default weighting is biased toward Reasoning + Coding + Tool Use,
    which matches the priorities of most serious AI tinkerers.
    """
    if weights is None:
        weights = {
            BenchmarkType.REASONING: 0.32,
            BenchmarkType.CODING: 0.25,
            BenchmarkType.TOOL_USE: 0.18,
            BenchmarkType.GENERAL_INTELLIGENCE: 0.15,
            BenchmarkType.CONTEXT: 0.07,
            BenchmarkType.SPEED: 0.03,
        }

    if not snapshot.benchmarks:
        return 0.0

    weighted_sum = 0.0
    total_weight = 0.0

    for btype, score in snapshot.benchmarks.items():
        w = weights.get(btype, 0.05)
        weighted_sum += score * w
        total_weight += w

    if total_weight == 0:
        return 0.0

    avg_benchmark = weighted_sum / total_weight
    total_price = snapshot.input_price + snapshot.output_price

    if total_price <= 0:
        return avg_benchmark * 100  # Arbitrary high value if free

    # Value Score = (Weighted benchmark performance) / (Price per million tokens)
    # We scale it for readability
    value_score = (avg_benchmark / total_price) * 10
    return round(value_score, 2)


def calculate_price_change_pct(
    start_price: float,
    end_price: float
) -> float:
    """Calculate percentage change in total price."""
    if start_price == 0:
        return 0.0
    return round(((end_price - start_price) / start_price) * 100, 2)


def calculate_value_trend(
    model_id: str,
    snapshots: List[ModelSnapshot],
    window_days: int = 90,
    weights: Optional[Dict[BenchmarkType, float]] = None
) -> Optional[ValueTrend]:
    """
    Calculate how a model's value has changed over a time window.

    This is one of the most important analytical outputs in the deeper MVP.
    """
    if len(snapshots) < 2:
        return None

    # Sort snapshots by date (oldest first)
    sorted_snapshots = sorted(snapshots, key=lambda s: s.date)

    end_date = sorted_snapshots[-1].date
    start_date = end_date - timedelta(days=window_days)

    # Find closest snapshots to the window boundaries
    start_snapshot = None
    end_snapshot = sorted_snapshots[-1]

    for snap in sorted_snapshots:
        if snap.date >= start_date:
            start_snapshot = snap
            break

    if start_snapshot is None or start_snapshot == end_snapshot:
        return None

    # Compute value scores at both points
    start_score = calculate_value_score(start_snapshot, weights)
    end_score = calculate_value_score(end_snapshot, weights)

    value_change = end_score - start_score
    value_improved = value_change > 0

    # Price movement
    start_total_price = start_snapshot.input_price + start_snapshot.output_price
    end_total_price = end_snapshot.input_price + end_snapshot.output_price
    price_change_pct = calculate_price_change_pct(start_total_price, end_total_price)

    # Benchmark movement (simplified for MVP)
    benchmark_movement: Dict[BenchmarkType, float] = {}
    for btype in BenchmarkType:
        if btype in start_snapshot.benchmarks and btype in end_snapshot.benchmarks:
            delta = end_snapshot.benchmarks[btype] - start_snapshot.benchmarks[btype]
            benchmark_movement[btype] = round(delta, 2)

    # Generate human-readable summary
    if value_improved and price_change_pct < -10:
        summary = f"Significantly better value: price dropped {abs(price_change_pct)}% while performance held or improved."
    elif value_improved:
        summary = f"Improved value over time (+{round(value_change, 2)})."
    elif price_change_pct > 15 and not value_improved:
        summary = f"Worse value: price increased {price_change_pct}% with limited performance gains."
    else:
        summary = f"Relatively stable value over the period (change: {round(value_change, 2)})."

    return ValueTrend(
        model_id=model_id,
        window_days=window_days,
        start_date=start_snapshot.date,
        end_date=end_snapshot.date,
        start_price=start_total_price,
        end_price=end_total_price,
        price_change_pct=price_change_pct,
        benchmark_movement=benchmark_movement,
        value_improved=value_improved,
        value_change_score=round(value_change, 3),
        summary=summary
    )


def generate_value_trends_for_model(
    model_id: str,
    snapshots: List[ModelSnapshot],
    weights: Optional[Dict[BenchmarkType, float]] = None
) -> List[ValueTrend]:
    """Generate value trends for common time windows (30, 60, 90 days)."""
    trends = []
    for window in [30, 60, 90]:
        trend = calculate_value_trend(model_id, snapshots, window_days=window, weights=weights)
        if trend:
            trends.append(trend)
    return trends