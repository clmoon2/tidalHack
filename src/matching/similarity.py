"""
Similarity calculation for anomaly matching.

This module implements multi-criteria similarity scoring for matching anomalies
across inspection runs using distance, clock position, type, and dimensions.
"""

import math
from typing import Dict, Optional
from src.data_models.models import AnomalyRecord


class SimilarityCalculator:
    """
    Calculate multi-criteria similarity between anomalies.
    
    Uses exponential decay functions for continuous features and exact matching
    for categorical features. Combines multiple similarity components with
    configurable weights.
    
    Default weights:
        - distance: 0.35
        - clock: 0.20
        - type: 0.15
        - depth: 0.15
        - length: 0.075
        - width: 0.075
    """
    
    def __init__(
        self,
        distance_sigma: float = 5.0,
        clock_sigma: float = 1.0,
        dimension_sigma: Optional[float] = None,
        weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize similarity calculator with configurable parameters.
        
        Args:
            distance_sigma: Sigma parameter for distance similarity (feet)
            clock_sigma: Sigma parameter for clock position similarity
            dimension_sigma: Sigma parameter for dimension similarity (if None, uses relative difference)
            weights: Dictionary of weights for each similarity component
                    Keys: 'distance', 'clock', 'type', 'depth', 'length', 'width'
        """
        self.distance_sigma = distance_sigma
        self.clock_sigma = clock_sigma
        self.dimension_sigma = dimension_sigma
        
        # Default weights
        self.weights = {
            'distance': 0.35,
            'clock': 0.20,
            'type': 0.15,
            'depth': 0.15,
            'length': 0.075,
            'width': 0.075
        }
        
        # Update with custom weights if provided
        if weights:
            self.weights.update(weights)
        
        # Validate weights sum to 1.0
        total_weight = sum(self.weights.values())
        if not math.isclose(total_weight, 1.0, abs_tol=1e-6):
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    def distance_similarity(self, dist1: float, dist2: float) -> float:
        """
        Calculate distance similarity using exponential decay.
        
        Uses formula: exp(-(distance_diff / sigma)²)
        
        Args:
            dist1: Distance of first anomaly (feet)
            dist2: Distance of second anomaly (feet)
        
        Returns:
            Similarity score in [0, 1] where 1 is identical location
        """
        distance_diff = abs(dist1 - dist2)
        return math.exp(-((distance_diff / self.distance_sigma) ** 2))
    
    def clock_similarity(self, clock1: float, clock2: float) -> float:
        """
        Calculate clock position similarity with circular distance.
        
        Handles wraparound (12 o'clock → 1 o'clock is 1 hour, not 11 hours).
        Uses formula: exp(-(circular_distance / sigma)²)
        
        Args:
            clock1: Clock position of first anomaly (1-12)
            clock2: Clock position of second anomaly (1-12)
        
        Returns:
            Similarity score in [0, 1] where 1 is same clock position
        """
        # Calculate circular distance (minimum of clockwise and counter-clockwise)
        direct_distance = abs(clock1 - clock2)
        circular_distance = min(direct_distance, 12 - direct_distance)
        
        return math.exp(-((circular_distance / self.clock_sigma) ** 2))
    
    def type_similarity(self, type1: str, type2: str) -> float:
        """
        Calculate feature type similarity (exact match).
        
        Args:
            type1: Feature type of first anomaly
            type2: Feature type of second anomaly
        
        Returns:
            1.0 if types match, 0.0 otherwise
        """
        return 1.0 if type1 == type2 else 0.0
    
    def dimension_similarity(self, dim1: float, dim2: float) -> float:
        """
        Calculate dimension similarity using exponential decay.
        
        If dimension_sigma is set, uses: exp(-(dimension_diff / sigma)²)
        Otherwise uses relative difference: exp(-(|dim1 - dim2| / (dim1 + dim2 + epsilon))²)
        
        Args:
            dim1: Dimension value of first anomaly
            dim2: Dimension value of second anomaly
        
        Returns:
            Similarity score in [0, 1] where 1 is identical dimension
        """
        if self.dimension_sigma is not None:
            # Absolute difference with sigma
            dimension_diff = abs(dim1 - dim2)
            return math.exp(-((dimension_diff / self.dimension_sigma) ** 2))
        else:
            # Relative difference (scale-invariant)
            epsilon = 1e-6  # Prevent division by zero
            relative_diff = abs(dim1 - dim2) / (dim1 + dim2 + epsilon)
            return math.exp(-(relative_diff ** 2))
    
    def calculate_similarity(
        self,
        anomaly1: AnomalyRecord,
        anomaly2: AnomalyRecord,
        use_corrected_distance: bool = False
    ) -> Dict[str, float]:
        """
        Calculate overall similarity between two anomalies.
        
        Combines multiple similarity components using weighted sum:
        - Distance similarity (corrected or original)
        - Clock position similarity (with circular distance)
        - Feature type similarity (exact match)
        - Depth similarity
        - Length similarity
        - Width similarity
        
        Args:
            anomaly1: First anomaly record
            anomaly2: Second anomaly record
            use_corrected_distance: If True, use corrected_distance field if available
        
        Returns:
            Dictionary containing:
                - 'overall': Overall weighted similarity score [0, 1]
                - 'distance': Distance similarity component
                - 'clock': Clock position similarity component
                - 'type': Feature type similarity component
                - 'depth': Depth similarity component
                - 'length': Length similarity component
                - 'width': Width similarity component
        """
        # Get distances (use corrected if available and requested)
        dist1 = anomaly1.distance
        dist2 = anomaly2.distance
        
        if use_corrected_distance:
            # Check if anomalies have corrected_distance attribute
            if hasattr(anomaly1, 'corrected_distance') and anomaly1.corrected_distance is not None:
                dist1 = anomaly1.corrected_distance
            if hasattr(anomaly2, 'corrected_distance') and anomaly2.corrected_distance is not None:
                dist2 = anomaly2.corrected_distance
        
        # Calculate individual similarity components
        dist_sim = self.distance_similarity(dist1, dist2)
        clock_sim = self.clock_similarity(anomaly1.clock_position, anomaly2.clock_position)
        type_sim = self.type_similarity(anomaly1.feature_type, anomaly2.feature_type)
        depth_sim = self.dimension_similarity(anomaly1.depth_pct, anomaly2.depth_pct)
        length_sim = self.dimension_similarity(anomaly1.length, anomaly2.length)
        width_sim = self.dimension_similarity(anomaly1.width, anomaly2.width)
        
        # Calculate weighted overall similarity
        overall_sim = (
            self.weights['distance'] * dist_sim +
            self.weights['clock'] * clock_sim +
            self.weights['type'] * type_sim +
            self.weights['depth'] * depth_sim +
            self.weights['length'] * length_sim +
            self.weights['width'] * width_sim
        )
        
        return {
            'overall': overall_sim,
            'distance': dist_sim,
            'clock': clock_sim,
            'type': type_sim,
            'depth': depth_sim,
            'length': length_sim,
            'width': width_sim
        }
