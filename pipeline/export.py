"""
RouteVault - Data Export Engine

Responsible for taking raw models, price history, benchmark history,
and computed analytical objects, then producing rich, frontend-ready
JSON datasets for the Deeper Analytical MVP.
"""

from datetime import datetime
from typing import List, Dict, Optional
from .schema import (
    Model,
    ModelSnapshot,
    PriceSnapshot,
    BenchmarkSnapshot,
    ValueTrend,
    ModelDataset,
)


def build_model_dataset(
    models: List[Model],
    latest_snapshots: List[ModelSnapshot],
    historical_price_data: Dict[str, List[PriceSnapshot]],
    benchmark_history: Dict[str, List[BenchmarkSnapshot]],
    value_trends_30d: List[ValueTrend],
    value_trends_60d: List[ValueTrend],
    value_trends_90d: List[ValueTrend],
) -> ModelDataset:
    """
    Assemble the master dataset that powers the analytical frontend.

    This is the main output of the pipeline.
    """
    dataset = ModelDataset(
        generated_at=datetime.utcnow(),
        models=models,
        latest_snapshots=latest_snapshots,
        historical_price_data=historical_price_data,
        benchmark_history=benchmark_history,
        value_trends_30d=value_trends_30d,
        value_trends_60d=value_trends_60d,
        value_trends_90d=value_trends_90d,
    )
    return dataset


def export_dataset_to_json(
    dataset: ModelDataset,
    output_path: str = "data/routevault_analytical_dataset.json"
) -> str:
    """
    Export the full analytical dataset as JSON.

    The frontend (Models Explorer, Model Detail, Trends Dashboard) will
    primarily consume this file (or future split files).
    """
    with open(output_path, "w") as f:
        f.write(dataset.model_dump_json(indent=2))

    return output_path


def generate_lightweight_models_export(
    models: List[Model],
    latest_snapshots: List[ModelSnapshot],
    value_trends_90d: List[ValueTrend],
    output_path: str = "data/models_explorer.json"
) -> str:
    """
    Generate a lightweight, optimized export specifically for the
    main Models Explorer table.

    This will be the primary data source for the interactive table
    with sorting, filtering, and value trend columns.
    """
    # In a real implementation we would join these properly.
    # For now this is a stub that shows the intended shape.
    export_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "models": [m.model_dump() for m in models],
        "latest_snapshots": [s.model_dump() for s in latest_snapshots],
        "value_trends_90d": [t.model_dump() for t in value_trends_90d],
    }

    with open(output_path, "w") as f:
        import json
        json.dump(export_data, f, indent=2, default=str)

    return output_path