"""
Basic risk scoring for anomaly prioritization.

This module implements a simplified risk scoring algorithm for MVP,
combining depth, growth rate, and location factors.
"""

from typing import List, Dict, Optional
from src.data_models.models import AnomalyRecord, GrowthMetrics


class RiskScorer:
    """
    Calculate composite risk scores for anomaly prioritization.
    
    Risk formula: (depth/100)*0.6 + (growth_rate/10)*0.3 + location_factor*0.1
    
    An additional configurable boost is applied when an anomaly belongs to
    an ASME B31G interaction zone (``cluster_id`` is set).
    
    Components:
    - Depth contribution: 0-60% (current severity)
    - Growth rate contribution: 0-30% (future risk)
    - Location contribution: 0-10% (context)
    - Cluster boost: additive bump for clustered anomalies (capped at 1.0)
    """
    
    def __init__(
        self,
        depth_weight: float = 0.6,
        growth_weight: float = 0.3,
        location_weight: float = 0.1,
        cluster_boost: float = 0.1,
    ):
        """
        Initialize risk scorer with configurable weights.
        
        Args:
            depth_weight: Weight for depth contribution (default 0.6)
            growth_weight: Weight for growth rate contribution (default 0.3)
            location_weight: Weight for location contribution (default 0.1)
            cluster_boost: Additive risk boost for clustered anomalies (default 0.1)
        """
        # Validate weights sum to 1.0
        total = depth_weight + growth_weight + location_weight
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        
        self.depth_weight = depth_weight
        self.growth_weight = growth_weight
        self.location_weight = location_weight
        self.cluster_boost = cluster_boost
    
    def calculate_location_factor(
        self,
        anomaly: AnomalyRecord,
        reference_points: Optional[List[Dict]] = None
    ) -> float:
        """
        Calculate location risk factor based on proximity to reference points.
        
        Higher risk near girth welds, valves, and other critical features.
        
        Args:
            anomaly: Anomaly record
            reference_points: List of reference point dictionaries with 'distance' key
        
        Returns:
            Location factor in [0, 1] where 1 is highest risk
        """
        if reference_points is None or not reference_points:
            # Default moderate risk if no reference points available
            return 0.5
        
        # Find nearest reference point
        min_distance = float('inf')
        for ref_point in reference_points:
            distance_diff = abs(anomaly.distance - ref_point.get('distance', float('inf')))
            min_distance = min(min_distance, distance_diff)
        
        # Risk decreases with distance from reference points
        # High risk within 3 feet, moderate within 10 feet, low beyond
        if min_distance < 3.0:
            return 1.0  # High risk
        elif min_distance < 10.0:
            # Linear interpolation between 1.0 and 0.5
            return 1.0 - (min_distance - 3.0) / 7.0 * 0.5
        else:
            return 0.5  # Moderate baseline risk
    
    def composite_risk(
        self,
        depth_pct: float,
        growth_rate: float,
        location_factor: float
    ) -> float:
        """
        Calculate composite risk score.
        
        Formula: (depth/100)*depth_weight + (growth_rate/10)*growth_weight + location_factor*location_weight
        
        Args:
            depth_pct: Current depth as percentage (0-100)
            growth_rate: Growth rate as % per year
            location_factor: Location risk factor (0-1)
        
        Returns:
            Composite risk score in [0, 1]
        """
        # Normalize depth to [0, 1]
        depth_normalized = min(depth_pct / 100.0, 1.0)
        
        # Normalize growth rate to [0, 1] (cap at 10% per year)
        growth_normalized = min(growth_rate / 10.0, 1.0)
        
        # Calculate weighted sum
        risk_score = (
            depth_normalized * self.depth_weight +
            growth_normalized * self.growth_weight +
            location_factor * self.location_weight
        )
        
        return risk_score
    
    def score_anomaly(
        self,
        anomaly: AnomalyRecord,
        growth_metrics: Optional[GrowthMetrics] = None,
        reference_points: Optional[List[Dict]] = None
    ) -> Dict[str, float]:
        """
        Calculate risk score for a single anomaly.
        
        If the anomaly has a non-null ``cluster_id`` (i.e. it belongs to an
        ASME B31G interaction zone), an additive ``cluster_boost`` is applied
        to the composite risk score (capped at 1.0).
        
        Args:
            anomaly: Anomaly record
            growth_metrics: Growth metrics (if available)
            reference_points: Reference points for location factor
        
        Returns:
            Dictionary with risk score components and total
        """
        # Get growth rate (0 if not available)
        growth_rate = 0.0
        if growth_metrics is not None:
            growth_rate = growth_metrics.depth_growth_rate
        
        # Calculate location factor
        location_factor = self.calculate_location_factor(anomaly, reference_points)
        
        # Calculate composite risk
        risk_score = self.composite_risk(
            anomaly.depth_pct,
            growth_rate,
            location_factor
        )

        # Apply cluster boost if anomaly is in an interaction zone
        is_clustered = getattr(anomaly, "cluster_id", None) is not None
        cluster_contribution = 0.0
        if is_clustered:
            cluster_contribution = self.cluster_boost
            risk_score = min(risk_score + cluster_contribution, 1.0)
        
        return {
            'anomaly_id': anomaly.id,
            'risk_score': risk_score,
            'depth_pct': anomaly.depth_pct,
            'growth_rate': growth_rate,
            'location_factor': location_factor,
            'depth_contribution': (anomaly.depth_pct / 100.0) * self.depth_weight,
            'growth_contribution': min(growth_rate / 10.0, 1.0) * self.growth_weight,
            'location_contribution': location_factor * self.location_weight,
            'cluster_contribution': cluster_contribution,
            'is_clustered': is_clustered,
        }
    
    def score_anomalies(
        self,
        anomalies: List[AnomalyRecord],
        growth_metrics_list: Optional[List[GrowthMetrics]] = None,
        reference_points: Optional[List[Dict]] = None
    ) -> List[Dict[str, float]]:
        """
        Calculate risk scores for multiple anomalies.
        
        Args:
            anomalies: List of anomaly records
            growth_metrics_list: List of growth metrics (optional)
            reference_points: Reference points for location factor
        
        Returns:
            List of risk score dictionaries
        """
        # Create lookup for growth metrics
        # Match IDs are in format: "{anom1.id}_{anom2.id}"
        # Example: "RUN_2015_123_RUN_2022_456"
        # We need to extract anom2.id (the newer run anomaly)
        growth_lookup = {}
        if growth_metrics_list:
            for gm in growth_metrics_list:
                # The match_id from GrowthMetrics.match_id is actually the Match.id
                # which is formatted as f"{anom1.id}_{anom2.id}"
                # We need to find where the second ID starts
                
                # Split and look for the second occurrence of "RUN"
                parts = gm.match_id.split('_')
                run_indices = [i for i, p in enumerate(parts) if p.startswith('RUN')]
                
                if len(run_indices) >= 2:
                    # Second RUN starts the second anomaly ID
                    second_run_start = run_indices[1]
                    anomaly2_id = '_'.join(parts[second_run_start:])
                    growth_lookup[anomaly2_id] = gm
                elif len(run_indices) == 1:
                    # Only one RUN found, might be simple format
                    # Try splitting in half
                    mid = len(parts) // 2
                    anomaly2_id = '_'.join(parts[mid:])
                    growth_lookup[anomaly2_id] = gm
        
        # Score each anomaly
        scores = []
        for anomaly in anomalies:
            growth_metrics = growth_lookup.get(anomaly.id)
            score = self.score_anomaly(anomaly, growth_metrics, reference_points)
            scores.append(score)
        
        return scores
    
    def rank_by_risk(
        self,
        anomalies: List[AnomalyRecord],
        growth_metrics_list: Optional[List[GrowthMetrics]] = None,
        reference_points: Optional[List[Dict]] = None,
        top_n: Optional[int] = None
    ) -> List[Dict[str, any]]:
        """
        Rank anomalies by risk score (highest first).
        
        Args:
            anomalies: List of anomaly records
            growth_metrics_list: List of growth metrics (optional)
            reference_points: Reference points for location factor
            top_n: Return only top N anomalies (optional)
        
        Returns:
            List of risk score dictionaries sorted by risk (descending)
        """
        # Calculate scores
        scores = self.score_anomalies(anomalies, growth_metrics_list, reference_points)
        
        # Sort by risk score (descending)
        sorted_scores = sorted(scores, key=lambda x: x['risk_score'], reverse=True)
        
        # Return top N if specified
        if top_n is not None:
            return sorted_scores[:top_n]
        
        return sorted_scores
    
    def get_high_risk_anomalies(
        self,
        anomalies: List[AnomalyRecord],
        growth_metrics_list: Optional[List[GrowthMetrics]] = None,
        reference_points: Optional[List[Dict]] = None,
        threshold: float = 0.7
    ) -> List[Dict[str, any]]:
        """
        Get anomalies exceeding risk threshold.
        
        Args:
            anomalies: List of anomaly records
            growth_metrics_list: List of growth metrics (optional)
            reference_points: Reference points for location factor
            threshold: Risk score threshold (default 0.7)
        
        Returns:
            List of high-risk anomalies with scores
        """
        # Calculate scores
        scores = self.score_anomalies(anomalies, growth_metrics_list, reference_points)
        
        # Filter by threshold
        high_risk = [score for score in scores if score['risk_score'] >= threshold]
        
        # Sort by risk score (descending)
        high_risk_sorted = sorted(high_risk, key=lambda x: x['risk_score'], reverse=True)
        
        return high_risk_sorted

