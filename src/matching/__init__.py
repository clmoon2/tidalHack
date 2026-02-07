"""
Anomaly matching engine using similarity scoring and Hungarian algorithm.
"""

from src.matching.similarity import SimilarityCalculator
from src.matching.matcher import (
    HungarianMatcher,
    MatchConfidence,
    UnmatchedClassification
)

__all__ = [
    'SimilarityCalculator',
    'HungarianMatcher',
    'MatchConfidence',
    'UnmatchedClassification'
]
