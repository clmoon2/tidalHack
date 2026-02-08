"""
Inspection interval calculator per regulatory requirements.
"""

from typing import Dict, Optional
from enum import Enum


class IntervalBasis(str, Enum):
    """Basis for inspection interval calculation."""
    TIME_TO_CRITICAL = "TIME_TO_CRITICAL"      # Based on growth rate
    REGULATORY_MAXIMUM = "REGULATORY_MAXIMUM"  # Capped by regulation
    ZERO_GROWTH = "ZERO_GROWTH"                # No growth detected
    NEGATIVE_GROWTH = "NEGATIVE_GROWTH"        # Decreasing depth


class InspectionIntervalCalculator:
    """
    Calculate inspection intervals per regulatory requirements.
    
    Implements:
    - 49 CFR 192.933 (Federal Pipeline Safety)
    - ASME B31.8S (Gas Pipeline Safety Management)
    
    Rules:
    - 50% safety factor applied to time-to-critical
    - Maximum 5 years for HCA (High Consequence Area)
    - Maximum 7 years for non-HCA
    - Minimum 1 year for any anomaly
    """
    
    def __init__(
        self,
        safety_factor: float = 0.5,
        hca_max_years: float = 5.0,
        non_hca_max_years: float = 7.0,
        min_years: float = 1.0,
        critical_threshold: float = 80.0
    ):
        """
        Initialize inspection interval calculator.
        
        Args:
            safety_factor: Safety factor (default 0.5 = 50%)
            hca_max_years: Maximum interval for HCA (default 5 years)
            non_hca_max_years: Maximum interval for non-HCA (default 7 years)
            min_years: Minimum interval (default 1 year)
            critical_threshold: Critical depth threshold (default 80%)
        """
        self.safety_factor = safety_factor
        self.hca_max_years = hca_max_years
        self.non_hca_max_years = non_hca_max_years
        self.min_years = min_years
        self.critical_threshold = critical_threshold
    
    def calculate_time_to_critical(
        self,
        current_depth: float,
        growth_rate: float
    ) -> Optional[float]:
        """
        Calculate time until anomaly reaches critical depth.
        
        Formula: (critical_threshold - current_depth) / growth_rate
        
        Args:
            current_depth: Current depth percentage
            growth_rate: Growth rate in percentage points per year
        
        Returns:
            Years to critical depth, or None if not applicable
        """
        if growth_rate <= 0:
            return None  # No growth or decreasing
        
        if current_depth >= self.critical_threshold:
            return 0.0  # Already critical
        
        remaining_depth = self.critical_threshold - current_depth
        time_to_critical = remaining_depth / growth_rate
        
        return time_to_critical
    
    def apply_safety_factor(self, time_to_critical: float) -> float:
        """
        Apply safety factor to time-to-critical.
        
        Args:
            time_to_critical: Calculated time to critical
        
        Returns:
            Time with safety factor applied
        """
        return time_to_critical * self.safety_factor
    
    def apply_regulatory_maximum(
        self,
        interval: float,
        is_hca: bool
    ) -> float:
        """
        Apply regulatory maximum interval.
        
        Per 49 CFR 192.933:
        - HCA: Maximum 5 years
        - Non-HCA: Maximum 7 years
        
        Args:
            interval: Calculated interval
            is_hca: Whether in High Consequence Area
        
        Returns:
            Interval capped at regulatory maximum
        """
        max_interval = self.hca_max_years if is_hca else self.non_hca_max_years
        return min(interval, max_interval)
    
    def calculate_inspection_interval(
        self,
        current_depth: float,
        growth_rate: float,
        is_hca: bool = False
    ) -> Dict:
        """
        Calculate inspection interval with all factors.
        
        Process:
        1. Calculate time to critical depth
        2. Apply 50% safety factor
        3. Apply regulatory maximum (5yr HCA, 7yr non-HCA)
        4. Apply minimum (1 year)
        
        Args:
            current_depth: Current depth percentage
            growth_rate: Growth rate in pp/year
            is_hca: Whether in High Consequence Area
        
        Returns:
            Dictionary with interval and calculation details
        """
        # Handle special cases
        if current_depth >= self.critical_threshold:
            return {
                'interval_years': 0.0,
                'basis': IntervalBasis.TIME_TO_CRITICAL.value,
                'time_to_critical': 0.0,
                'with_safety_factor': 0.0,
                'regulatory_maximum': self.hca_max_years if is_hca else self.non_hca_max_years,
                'final_interval': 0.0,
                'is_hca': is_hca,
                'note': 'Already at critical depth - immediate action required'
            }
        
        # Calculate time to critical
        time_to_critical = self.calculate_time_to_critical(current_depth, growth_rate)
        
        if time_to_critical is None or time_to_critical <= 0:
            # Zero or negative growth - use regulatory maximum
            regulatory_max = self.hca_max_years if is_hca else self.non_hca_max_years
            
            basis = (
                IntervalBasis.ZERO_GROWTH if growth_rate == 0
                else IntervalBasis.NEGATIVE_GROWTH
            )
            
            return {
                'interval_years': regulatory_max,
                'basis': basis.value,
                'time_to_critical': None,
                'with_safety_factor': None,
                'regulatory_maximum': regulatory_max,
                'final_interval': regulatory_max,
                'is_hca': is_hca,
                'note': f'No active growth - using regulatory maximum ({regulatory_max} years)'
            }
        
        # Apply safety factor
        with_safety = self.apply_safety_factor(time_to_critical)
        
        # Apply regulatory maximum
        regulatory_max = self.hca_max_years if is_hca else self.non_hca_max_years
        with_reg_max = self.apply_regulatory_maximum(with_safety, is_hca)
        
        # Apply minimum
        final_interval = max(with_reg_max, self.min_years)
        
        # Determine basis
        if final_interval == self.min_years:
            basis = IntervalBasis.TIME_TO_CRITICAL
            note = f'Rapid growth - minimum interval ({self.min_years} year) applied'
        elif final_interval == regulatory_max:
            basis = IntervalBasis.REGULATORY_MAXIMUM
            note = f'Capped at regulatory maximum ({regulatory_max} years for {"HCA" if is_hca else "non-HCA"})'
        else:
            basis = IntervalBasis.TIME_TO_CRITICAL
            note = f'Based on time to critical with {int(self.safety_factor*100)}% safety factor'
        
        return {
            'interval_years': final_interval,
            'basis': basis.value,
            'time_to_critical': time_to_critical,
            'with_safety_factor': with_safety,
            'regulatory_maximum': regulatory_max,
            'final_interval': final_interval,
            'is_hca': is_hca,
            'note': note
        }
    
    def determine_interval_basis(self, calculation: Dict) -> str:
        """
        Get human-readable explanation of interval basis.
        
        Args:
            calculation: Result from calculate_inspection_interval
        
        Returns:
            Human-readable explanation
        """
        return calculation.get('note', 'Interval calculated per regulatory requirements')
    
    def batch_calculate(
        self,
        anomalies_data: list
    ) -> list:
        """
        Calculate intervals for multiple anomalies.
        
        Args:
            anomalies_data: List of dicts with keys:
                - anomaly_id
                - current_depth
                - growth_rate
                - is_hca (optional, default False)
        
        Returns:
            List of interval calculations with anomaly IDs
        """
        results = []
        
        for data in anomalies_data:
            interval = self.calculate_inspection_interval(
                current_depth=data['current_depth'],
                growth_rate=data['growth_rate'],
                is_hca=data.get('is_hca', False)
            )
            
            interval['anomaly_id'] = data['anomaly_id']
            results.append(interval)
        
        return results

