"""
RouteVault - Core Data Schema for the Deeper Analytical MVP

This module defines the fundamental data models used for deep historical
price + performance analysis of AI models.

Design Goals:
- Support rich historical snapshots (price + multiple benchmarks)
- Enable computation of value trends over time
- Be clear and extensible
- Work well with both static JSON exports and future database use
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class RouteVaultLabel(str, Enum):
    """Consumer-friendly categories (from How do we weight models.md)"""
    RESEARCHER = "Researcher"
    PROJECT_PLANNER = "Project Planner"
    SENIOR_DEV = "Senior Developer"
    JUNIOR_DEV = "Junior Developer"
    BUDGET_EVERYDAY = "Budget Everyday"
    CREATIVE = "Creative Writer"
    SPECIALIST = "Specialist"
    UNKNOWN = "Unknown"


class BenchmarkType(str, Enum):
    """Core benchmarks we track for analytical depth"""
    REASONING = "reasoning"
    CODING = "coding"
    TOOL_USE = "tool_use"
    GENERAL_INTELLIGENCE = "general_intelligence"
    CONTEXT = "context"
    SPEED = "speed"
    MULTIMODAL = "multimodal"


class PriceSnapshot(BaseModel):
    """A single point-in-time price record for a model"""
    model_id: str
    date: date
    input_price: float = Field(..., description="Price per million input tokens (USD)")
    output_price: float = Field(..., description="Price per million output tokens (USD)")

    @property
    def total_price(self) -> float:
        return self.input_price + self.output_price


class BenchmarkSnapshot(BaseModel):
    """A single benchmark score for a model at a point in time"""
    model_id: str
    date: date
    benchmark_type: BenchmarkType
    score: float
    source: Optional[str] = None
    notes: Optional[str] = None


class Model(BaseModel):
    """
    Core model entity.
    Contains relatively stable information + current state.
    """
    model_id: str
    provider: str
    rv_label: RouteVaultLabel = RouteVaultLabel.UNKNOWN
    context_k: int = Field(..., description="Context window in thousands of tokens")
    release_date: Optional[date] = None

    # Current pricing (latest known)
    current_input_price: float
    current_output_price: float

    # Optional metadata
    description: Optional[str] = None
    is_deprecated: bool = False


class ModelSnapshot(BaseModel):
    """
    A point-in-time view of a model.

    This is the key analytical object. It combines price + benchmarks
    at a specific date and includes derived metrics.
    """
    model_id: str
    date: date

    # Pricing at this snapshot
    input_price: float
    output_price: float

    # Benchmarks at this snapshot (key-value for flexibility)
    benchmarks: Dict[BenchmarkType, float] = Field(default_factory=dict)

    # Derived metrics (computed)
    total_price: float = Field(default=0.0)
    value_score: Optional[float] = None          # Composite score
    price_performance_ratio: Optional[float] = None

    def compute_derived(self, weights: Optional[Dict[BenchmarkType, float]] = None):
        """Compute derived analytical fields"""
        self.total_price = self.input_price + self.output_price

        if self.benchmarks:
            # Simple default weighting if none provided
            if weights is None:
                weights = {
                    BenchmarkType.REASONING: 0.35,
                    BenchmarkType.CODING: 0.25,
                    BenchmarkType.TOOL_USE: 0.20,
                    BenchmarkType.GENERAL_INTELLIGENCE: 0.15,
                    BenchmarkType.CONTEXT: 0.05,
                }

            weighted_sum = 0.0
            total_weight = 0.0

            for btype, score in self.benchmarks.items():
                w = weights.get(btype, 0.1)
                weighted_sum += score * w
                total_weight += w

            if total_weight > 0:
                avg_benchmark = weighted_sum / total_weight
                # Higher is better. We want high benchmark score + low price
                if self.total_price > 0:
                    self.price_performance_ratio = avg_benchmark / self.total_price
                else:
                    self.price_performance_ratio = avg_benchmark


class ValueTrend(BaseModel):
    """
    Represents how a model's value has changed over a time window.
    This is one of the most important analytical outputs.
    """
    model_id: str
    window_days: int  # 30, 60, 90, etc.

    start_date: date
    end_date: date

    start_price: float
    end_price: float
    price_change_pct: float

    # Average benchmark movement (if we have data)
    benchmark_movement: Dict[BenchmarkType, float] = Field(default_factory=dict)

    # Overall value trend
    value_improved: bool
    value_change_score: float  # Positive = better value over time
    summary: str


class ModelAnalysis(BaseModel):
    """
    Rich analytical view of a single model.
    This is what powers the deep "Model Intelligence" page.
    """
    model: Model
    latest_snapshot: ModelSnapshot
    historical_snapshots: List[ModelSnapshot] = Field(default_factory=list)
    trends: List[ValueTrend] = Field(default_factory=list)

    # High-level insights
    price_trend_summary: Optional[str] = None
    value_trend_summary: Optional[str] = None


# =============================================================================
# Collection / Dataset Models
# =============================================================================

class ModelDataset(BaseModel):
    """
    The main dataset object that the frontend will consume.
    Contains everything needed for the analytical explorer.
    """
    generated_at: datetime
    models: List[Model]
    latest_snapshots: List[ModelSnapshot]
    historical_price_data: Dict[str, List[PriceSnapshot]] = Field(default_factory=dict)
    benchmark_history: Dict[str, List[BenchmarkSnapshot]] = Field(default_factory=dict)

    # Pre-computed analytical views (very useful for frontend)
    value_trends_30d: List[ValueTrend] = Field(default_factory=list)
    value_trends_60d: List[ValueTrend] = Field(default_factory=list)
    value_trends_90d: List[ValueTrend] = Field(default_factory=list)