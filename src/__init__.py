"""
ILI Data Alignment & Corrosion Growth Prediction System

A hybrid system combining proven algorithms (DTW, Hungarian, XGBoost) with 
LLM-augmented capabilities for pipeline corrosion analysis.
"""

__version__ = "0.1.0"
__author__ = "Pipeline Integrity Team"

# Package-level imports for convenience
from src.data_models import (
    AnomalyRecord,
    ReferencePoint,
    Match,
    GrowthMetrics,
    Prediction,
    AlignmentResult,
)

__all__ = [
    "AnomalyRecord",
    "ReferencePoint",
    "Match",
    "GrowthMetrics",
    "Prediction",
    "AlignmentResult",
]
