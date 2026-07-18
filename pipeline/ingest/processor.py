"""
RouteVault - Data Ingestion & Processing Pipeline (Improved)

This module is responsible for taking raw data (price history, benchmark history)
and producing rich analytical objects (ModelSnapshots, ValueTrends, etc.).
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

from ..schema import (
    Model,
    ModelSnapshot,
    PriceSnapshot,
    BenchmarkSnapshot,
    ValueTrend,
    RouteVaultLabel,
    BenchmarkType,
)
from ..compute import generate_value_trends_for_model


class RouteVaultProcessor:
    """Main processor for turning raw RouteVault data into analytical datasets."""

    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = Path(data_dir)
        self.models: List[Model] = []
        self.price_history: Dict[str, List[PriceSnapshot]] = {}
        self.benchmark_history: Dict[str, List[BenchmarkSnapshot]] = {}

    def load_from_models_json(self, filename: str = "models.json") -> None:
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Could not find {filepath}")

        with open(filepath, "r") as f:
            raw_data = json.load(f)

        for m in raw_data.get("models", []):
            model = Model(
                model_id=m["model_id"],
                provider=m["provider"],
                rv_label=self._parse_rv_label(m.get("rv_label")),
                context_k=m["context_k"],
                current_input_price=m["current_input_price"],
                current_output_price=m["current_output_price"],
            )
            self.models.append(model)

            snapshots = []
            for ph in m.get("price_history", []):
                snapshot = PriceSnapshot(
                    model_id=m["model_id"],
                    date=datetime.fromisoformat(ph["date"]).date(),
                    input_price=ph["input"],
                    output_price=ph["output"],
                )
                snapshots.append(snapshot)

            self.price_history[m["model_id"]] = snapshots

    def _parse_rv_label(self, label: str | None) -> RouteVaultLabel:
        if not label:
            return RouteVaultLabel.UNKNOWN
        mapping = {
            "researcher": RouteVaultLabel.RESEARCHER,
            "project planner": RouteVaultLabel.PROJECT_PLANNER,
            "senior developer": RouteVaultLabel.SENIOR_DEV,
            "senior dev": RouteVaultLabel.SENIOR_DEV,
            "junior developer": RouteVaultLabel.JUNIOR_DEV,
            "junior dev": RouteVaultLabel.JUNIOR_DEV,
            "budget everyday": RouteVaultLabel.BUDGET_EVERYDAY,
            "creative writer": RouteVaultLabel.CREATIVE,
            "specialist": RouteVaultLabel.SPECIALIST,
        }
        return mapping.get(label.lower(), RouteVaultLabel.UNKNOWN)

    def generate_snapshots(self, add_synthetic_benchmarks: bool = False) -> List[ModelSnapshot]:
        """
        Generate ModelSnapshot objects.

        If add_synthetic_benchmarks=True, we inject simple simulated benchmark scores
        so the deeper analytical features (value trends) can be demonstrated even
        before real benchmark history is available.
        """
        snapshots = []

        for model in self.models:
            history = self.price_history.get(model.model_id, [])
            for i, price_snap in enumerate(history):
                benchmarks = {}

                if add_synthetic_benchmarks:
                    # Very rough synthetic data for demonstration
                    base = 70 + (hash(model.model_id) % 20)
                    # Add some variation over time
                    variation = (i % 7) - 3
                    benchmarks[BenchmarkType.REASONING] = base + variation
                    benchmarks[BenchmarkType.CODING] = base + (variation // 2)
                    benchmarks[BenchmarkType.TOOL_USE] = base - 5 + variation

                snap = ModelSnapshot(
                    model_id=model.model_id,
                    date=price_snap.date,
                    input_price=price_snap.input_price,
                    output_price=price_snap.output_price,
                    benchmarks=benchmarks,
                )
                snap.compute_derived()
                snapshots.append(snap)

        return snapshots

    def generate_value_trends(
        self, snapshots: List[ModelSnapshot]
    ) -> Dict[int, List[ValueTrend]]:
        trends_by_window: Dict[int, List[ValueTrend]] = {30: [], 60: [], 90: []}

        by_model: Dict[str, List[ModelSnapshot]] = {}
        for snap in snapshots:
            by_model.setdefault(snap.model_id, []).append(snap)

        for model_id, model_snaps in by_model.items():
            all_trends = generate_value_trends_for_model(model_id, model_snaps)
            for t in all_trends:
                if t.window_days in trends_by_window:
                    trends_by_window[t.window_days].append(t)

        return trends_by_window

    def build_full_dataset(self) -> Dict:
        print("Loading models.json...")
        self.load_from_models_json()
        print(f"Loaded {len(self.models)} models.")

        print("Generating snapshots (with synthetic benchmarks for demo)...")
        snapshots = self.generate_snapshots(add_synthetic_benchmarks=True)
        print(f"Generated {len(snapshots)} snapshots.")

        # Group snapshots by model to get latest per model
        snapshots_by_model: Dict[str, List[ModelSnapshot]] = {}
        for snap in snapshots:
            snapshots_by_model.setdefault(snap.model_id, []).append(snap)

        latest_snapshots = []
        for model in self.models:
            model_snaps = snapshots_by_model.get(model.model_id, [])
            if model_snaps:
                latest = max(model_snaps, key=lambda s: s.date)
                latest_snapshots.append(latest)

        print("Calculating value trends...")
        trends = self.generate_value_trends(snapshots)

        dataset = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_count": len(self.models),
            "snapshot_count": len(snapshots),
            "trends_30d_count": len(trends[30]),
            "trends_60d_count": len(trends[60]),
            "trends_90d_count": len(trends[90]),
            "models": [m.model_dump() for m in self.models],
            "latest_snapshots": [s.model_dump() for s in latest_snapshots],
            "value_trends_30d": [t.model_dump() for t in trends[30]],
            "value_trends_60d": [t.model_dump() for t in trends[60]],
            "value_trends_90d": [t.model_dump() for t in trends[90]],
        }

        return dataset


def main():
    processor = RouteVaultProcessor(
        data_dir=Path("/home/gumbyender/agents/routevault/data")
    )
    dataset = processor.build_full_dataset()

    output_path = Path("/home/gumbyender/agents/routevault/data/analytical_dataset.json")
    with open(output_path, "w") as f:
        json.dump(dataset, f, indent=2, default=str)

    print(f"\n✅ Analytical dataset written to: {output_path}")
    print(f"   Models: {dataset['model_count']}")
    print(f"   Snapshots: {dataset['snapshot_count']}")
    print(f"   Value trends (90d): {dataset['trends_90d_count']}")

    # Print interesting summary
    print("\n=== Top Value Changes (90 days) ===")
    sorted_trends = sorted(
        dataset["value_trends_90d"],
        key=lambda x: x["value_change_score"],
        reverse=True
    )

    print("\nBest value improvements:")
    for t in sorted_trends[:3]:
        print(f"  + {t['model_id']:<25} | Δ: {t['value_change_score']:>7.2f} | {t['summary']}")

    print("\nBiggest value regressions:")
    for t in sorted_trends[-3:]:
        print(f"  - {t['model_id']:<25} | Δ: {t['value_change_score']:>7.2f} | {t['summary']}")


if __name__ == "__main__":
    main()