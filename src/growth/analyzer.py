"""
Growth rate analysis for matched anomalies.

This module calculates growth rates for depth, length, and width dimensions
and identifies anomalies with rapid growth rates.
"""

from typing import List, Dict, Optional
from datetime import datetime
import statistics

from src.data_models.models import Match, AnomalyRecord, GrowthMetrics


class GrowthAnalyzer:
    """
    Analyze growth rates for matched anomalies.
    
    Calculates growth rates for depth, length, and width dimensions
    and identifies anomalies exceeding rapid growth thresholds.
    """
    
    def __init__(self, rapid_growth_threshold: float = 5.0):
        """
        Initialize growth analyzer.
        
        Args:
            rapid_growth_threshold: Threshold for rapid growth (% per year)
        """
        self.rapid_growth_threshold = rapid_growth_threshold
    
    def calculate_growth_rate(
        self,
        initial_value: float,
        final_value: float,
        time_interval_years: float
    ) -> float:
        """
        Calculate growth rate as absolute change per year.
        
        For depth (percentage), this returns percentage points per year.
        For dimensions (inches), this returns inches per year.
        
        Formula: (final - initial) / time_interval_years
        
        Args:
            initial_value: Initial measurement value
            final_value: Final measurement value
            time_interval_years: Time interval in years
        
        Returns:
            Growth rate as absolute change per year
        """
        if time_interval_years <= 0:
            raise ValueError("Time interval must be positive")
        
        # Calculate absolute change per year
        growth_rate = (final_value - initial_value) / time_interval_years
        
        return growth_rate
    
    def identify_rapid_growth(self, growth_rate: float) -> bool:
        """
        Identify if growth rate exceeds rapid growth threshold.
        
        Args:
            growth_rate: Growth rate (% per year)
        
        Returns:
            True if growth rate exceeds threshold
        """
        return growth_rate > self.rapid_growth_threshold
    
    def calculate_match_growth(
        self,
        anomaly_run1: AnomalyRecord,
        anomaly_run2: AnomalyRecord,
        time_interval_years: float
    ) -> GrowthMetrics:
        """
        Calculate growth metrics for a matched anomaly pair.
        
        Args:
            anomaly_run1: Anomaly from first (older) run
            anomaly_run2: Anomaly from second (newer) run
            time_interval_years: Time between inspections (years)
        
        Returns:
            GrowthMetrics object with calculated growth rates
        """
        # Calculate growth rates for each dimension
        depth_growth_rate = self.calculate_growth_rate(
            anomaly_run1.depth_pct,
            anomaly_run2.depth_pct,
            time_interval_years
        )
        
        length_growth_rate = self.calculate_growth_rate(
            anomaly_run1.length,
            anomaly_run2.length,
            time_interval_years
        )
        
        width_growth_rate = self.calculate_growth_rate(
            anomaly_run1.width,
            anomaly_run2.width,
            time_interval_years
        )
        
        # Identify rapid growth
        rapid_growth = self.identify_rapid_growth(depth_growth_rate)
        
        # Create GrowthMetrics object
        growth_metrics = GrowthMetrics(
            match_id=f"{anomaly_run1.id}_{anomaly_run2.id}",
            time_interval_years=time_interval_years,
            depth_growth_rate=depth_growth_rate,
            length_growth_rate=length_growth_rate,
            width_growth_rate=width_growth_rate,
            is_rapid_growth=rapid_growth,
            risk_score=0.0  # Will be calculated separately by RiskScorer
        )
        
        return growth_metrics
    
    def analyze_matches(
        self,
        matches: List[Match],
        anomalies_run1: List[AnomalyRecord],
        anomalies_run2: List[AnomalyRecord],
        time_interval_years: float
    ) -> Dict[str, any]:
        """
        Analyze growth for all matched anomalies.
        
        Args:
            matches: List of Match objects
            anomalies_run1: Anomalies from first run
            anomalies_run2: Anomalies from second run
            time_interval_years: Time between inspections (years)
        
        Returns:
            Dictionary containing:
                - 'growth_metrics': List of GrowthMetrics objects
                - 'statistics': Statistical summary of growth rates
                - 'rapid_growth_anomalies': List of anomalies with rapid growth
        """
        # Create lookup dictionaries for anomalies
        run1_lookup = {anom.id: anom for anom in anomalies_run1}
        run2_lookup = {anom.id: anom for anom in anomalies_run2}
        
        # Calculate growth metrics for each match
        growth_metrics_list = []
        rapid_growth_anomalies = []
        
        for match in matches:
            # Get anomaly records
            anom1 = run1_lookup.get(match.anomaly1_id)
            anom2 = run2_lookup.get(match.anomaly2_id)
            
            if anom1 is None or anom2 is None:
                continue  # Skip if anomaly not found
            
            # Calculate growth metrics
            growth_metrics = self.calculate_match_growth(
                anom1, anom2, time_interval_years
            )
            
            growth_metrics_list.append(growth_metrics)
            
            # Track rapid growth anomalies
            if growth_metrics.is_rapid_growth:
                rapid_growth_anomalies.append({
                    'anomaly_id': anom2.id,
                    'depth_growth_rate': growth_metrics.depth_growth_rate,
                    'current_depth': anom2.depth_pct,
                    'distance': anom2.distance,
                    'clock_position': anom2.clock_position
                })
        
        # Calculate statistical summaries
        statistics_summary = self._calculate_statistics(growth_metrics_list)
        
        return {
            'growth_metrics': growth_metrics_list,
            'statistics': statistics_summary,
            'rapid_growth_anomalies': rapid_growth_anomalies
        }
    
    def _calculate_statistics(
        self,
        growth_metrics_list: List[GrowthMetrics]
    ) -> Dict[str, any]:
        """
        Calculate statistical summaries for growth rates.
        
        Args:
            growth_metrics_list: List of GrowthMetrics objects
        
        Returns:
            Dictionary with statistical summaries
        """
        if not growth_metrics_list:
            return {
                'total_matches': 0,
                'rapid_growth_count': 0,
                'rapid_growth_percentage': 0.0,
                'depth_growth': {},
                'length_growth': {},
                'width_growth': {}
            }
        
        # Extract growth rates
        depth_rates = [gm.depth_growth_rate for gm in growth_metrics_list]
        length_rates = [gm.length_growth_rate for gm in growth_metrics_list]
        width_rates = [gm.width_growth_rate for gm in growth_metrics_list]
        
        # Count rapid growth
        rapid_growth_count = sum(1 for gm in growth_metrics_list if gm.is_rapid_growth)
        
        # Calculate statistics for each dimension
        def calc_stats(rates: List[float]) -> Dict[str, float]:
            if not rates:
                return {'mean': 0.0, 'median': 0.0, 'std_dev': 0.0, 'min': 0.0, 'max': 0.0}
            
            return {
                'mean': statistics.mean(rates),
                'median': statistics.median(rates),
                'std_dev': statistics.stdev(rates) if len(rates) > 1 else 0.0,
                'min': min(rates),
                'max': max(rates)
            }
        
        return {
            'total_matches': len(growth_metrics_list),
            'rapid_growth_count': rapid_growth_count,
            'rapid_growth_percentage': (rapid_growth_count / len(growth_metrics_list)) * 100,
            'depth_growth': calc_stats(depth_rates),
            'length_growth': calc_stats(length_rates),
            'width_growth': calc_stats(width_rates)
        }
    
    def get_growth_distribution_by_feature_type(
        self,
        growth_metrics_list: List[GrowthMetrics],
        anomalies_run2: List[AnomalyRecord]
    ) -> Dict[str, Dict[str, any]]:
        """
        Calculate growth rate distributions grouped by feature type.
        
        Args:
            growth_metrics_list: List of GrowthMetrics objects
            anomalies_run2: Anomalies from second run (for feature type lookup)
        
        Returns:
            Dictionary mapping feature_type to statistics
        """
        # Create lookup for feature types
        feature_type_lookup = {anom.id: anom.feature_type for anom in anomalies_run2}
        
        # Group growth metrics by feature type
        by_feature_type = {}
        
        for gm in growth_metrics_list:
            # Extract anomaly2_id from match_id (format: "id1_id2")
            anomaly2_id = gm.match_id.split('_', 1)[1] if '_' in gm.match_id else gm.match_id
            feature_type = feature_type_lookup.get(anomaly2_id, "unknown")
            
            if feature_type not in by_feature_type:
                by_feature_type[feature_type] = []
            
            by_feature_type[feature_type].append(gm)
        
        # Calculate statistics for each feature type
        result = {}
        for feature_type, metrics_list in by_feature_type.items():
            result[feature_type] = self._calculate_statistics(metrics_list)
        
        return result

