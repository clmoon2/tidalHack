"""
Regulatory risk scoring per 49 CFR and ASME B31.8S standards.
"""

from typing import Dict, Any
from src.data_models.models import (
    RegulatoryRiskScore,
    AnomalyWithRegulatory,
    RegulatoryThresholds,
)


class RegulatoryRiskScorer:
    """
    Calculate regulatory-compliant risk scores per 49 CFR 192.933 & ASME B31.8S.
    
    Risk scoring algorithm:
    - Depth contribution: 0-50 points
    - Growth rate contribution: 0-30 points
    - Location & context contribution: 0-20 points
    Total: 0-100 points
    """

    def calculate_depth_points(self, depth_pct: float) -> int:
        """
        Calculate depth contribution (0-50 points).
        
        Thresholds:
        - <30%: 10 points
        - 30-49%: 20 points
        - 50-79%: 35 points
        - ≥80%: 50 points
        
        Args:
            depth_pct: Depth as percentage of wall thickness
            
        Returns:
            Points (0-50)
        """
        if depth_pct < 30:
            return 10
        elif depth_pct < 50:
            return 20
        elif depth_pct < 80:
            return 35
        else:  # depth_pct >= 80
            return 50

    def calculate_growth_rate_points(self, growth_rate: float) -> int:
        """
        Calculate growth rate contribution (0-30 points).
        
        Thresholds per ASME B31.8S:
        - ≤0.5%/yr: 5 points (acceptable)
        - 0.5-2%/yr: 10 points (monitor)
        - 2-5%/yr: 20 points (moderate risk)
        - >5%/yr: 30 points (high risk)
        
        Args:
            growth_rate: Growth rate in % wall thickness per year
            
        Returns:
            Points (0-30)
        """
        if growth_rate <= RegulatoryThresholds.ASME_ACCEPTABLE_GROWTH:
            return 5
        elif growth_rate <= RegulatoryThresholds.ASME_MODERATE_GROWTH:
            return 10
        elif growth_rate <= RegulatoryThresholds.ASME_HIGH_GROWTH:
            return 20
        else:  # growth_rate > 5.0
            return 30

    def calculate_location_points(self, anomaly: AnomalyWithRegulatory) -> int:
        """
        Calculate location & context contribution (0-20 points).
        
        Factors:
        - HCA status: +8 points
        - Proximity to girth weld (<3 ft): +6 points
        - Poor coating condition: +6 points
        - Fair coating condition: +3 points
        
        Args:
            anomaly: Anomaly with location context
            
        Returns:
            Points (0-20)
        """
        points = 0

        # High Consequence Area
        if anomaly.is_hca:
            points += 8

        # Proximity to girth weld
        if anomaly.distance_to_nearest_weld_ft is not None:
            if anomaly.distance_to_nearest_weld_ft < 3.0:
                points += 6

        # Coating condition
        if anomaly.coating_condition == "poor":
            points += 6
        elif anomaly.coating_condition == "fair":
            points += 3

        return min(points, 20)  # Cap at 20

    def classify_risk_level(self, score: int) -> str:
        """
        Classify risk level based on total score.
        
        Thresholds:
        - ≥85: CRITICAL
        - ≥70: HIGH
        - ≥50: MODERATE
        - ≥30: LOW
        - <30: ACCEPTABLE
        
        Args:
            score: Total risk score (0-100)
            
        Returns:
            Risk level string
        """
        if score >= 85:
            return "CRITICAL"
        elif score >= 70:
            return "HIGH"
        elif score >= 50:
            return "MODERATE"
        elif score >= 30:
            return "LOW"
        else:
            return "ACCEPTABLE"

    def classify_cfr_action(self, depth_pct: float, maop_ratio: float = None) -> tuple[str, str]:
        """
        Classify action required per 49 CFR 192.933.
        
        Immediate action conditions:
        - Depth >80% of wall thickness
        - MAOP ratio <1.1
        
        Scheduled action conditions:
        - Depth 50-80% of wall thickness
        
        Args:
            depth_pct: Depth as percentage of wall thickness
            maop_ratio: Maximum Allowable Operating Pressure ratio
            
        Returns:
            Tuple of (classification, reference)
        """
        if depth_pct > RegulatoryThresholds.CFR_IMMEDIATE_DEPTH:
            return ("IMMEDIATE_ACTION", "49 CFR 192.933(a)(1)")

        if maop_ratio is not None and maop_ratio < RegulatoryThresholds.CFR_MAOP_RATIO:
            return ("IMMEDIATE_ACTION", "49 CFR 192.933(a)(2)")

        if depth_pct >= RegulatoryThresholds.CFR_SCHEDULED_DEPTH:
            return ("SCHEDULED_ACTION", "49 CFR 195.452")

        return ("MONITORING", "49 CFR 192.935")

    def classify_asme_growth_rate(self, growth_rate: float) -> tuple[str, str]:
        """
        Classify growth rate per ASME B31.8S standards.
        
        Thresholds:
        - ≤0.5%/yr: ACCEPTABLE
        - 0.5-2%/yr: ACCEPTABLE_MONITOR
        - 2-5%/yr: MODERATE_RISK
        - >5%/yr: HIGH_RISK
        
        Args:
            growth_rate: Growth rate in % wall thickness per year
            
        Returns:
            Tuple of (classification, reference)
        """
        if growth_rate <= RegulatoryThresholds.ASME_ACCEPTABLE_GROWTH:
            return ("ACCEPTABLE", "ASME B31.8S Section 5")
        elif growth_rate <= RegulatoryThresholds.ASME_MODERATE_GROWTH:
            return ("ACCEPTABLE_MONITOR", "ASME B31.8S Section 5")
        elif growth_rate <= RegulatoryThresholds.ASME_HIGH_GROWTH:
            return ("MODERATE_RISK", "ASME B31.8S Section 5")
        else:
            return ("HIGH_RISK", "ASME B31.8S Section 5")

    def _max_severity(self, current: str, new: str) -> str:
        """Helper to escalate action severity"""
        severity_order = ["Standard", "Monitor", "Scheduled", "Immediate"]
        try:
            current_idx = severity_order.index(current)
            new_idx = severity_order.index(new)
            return severity_order[max(current_idx, new_idx)]
        except ValueError:
            return new

    def calculate_total_risk_score(
        self, anomaly: AnomalyWithRegulatory, growth_rate: float
    ) -> RegulatoryRiskScore:
        """
        Calculate comprehensive regulatory risk score.
        
        Args:
            anomaly: Anomaly with regulatory context
            growth_rate: Growth rate in % wall thickness per year
            
        Returns:
            RegulatoryRiskScore with all classifications
        """
        # Calculate point contributions
        depth_points = self.calculate_depth_points(anomaly.depth_pct)
        growth_points = self.calculate_growth_rate_points(growth_rate)
        context_points = self.calculate_location_points(anomaly)

        # Total risk score
        total_score = min(depth_points + growth_points + context_points, 100)

        # Risk level classification
        risk_level = self.classify_risk_level(total_score)

        # CFR classification
        cfr_classification, cfr_reference = self.classify_cfr_action(
            anomaly.depth_pct, anomaly.maop_ratio
        )

        # ASME classification
        asme_classification, asme_reference = self.classify_asme_growth_rate(growth_rate)

        # Determine action required
        action = "Standard"
        basis = "ASME B31.8S"

        if anomaly.depth_pct > RegulatoryThresholds.CFR_IMMEDIATE_DEPTH:
            action = "Immediate"
            basis = "49 CFR 192.933(a)(1)"
        elif growth_rate > RegulatoryThresholds.ASME_HIGH_GROWTH:
            action = self._max_severity(action, "Immediate")
            basis += " + Growth Rate Threshold"
        elif anomaly.depth_pct >= RegulatoryThresholds.CFR_SCHEDULED_DEPTH:
            action = self._max_severity(action, "Scheduled")
            basis = "49 CFR 195.452"
        elif growth_rate > RegulatoryThresholds.ASME_MODERATE_GROWTH:
            action = self._max_severity(action, "Scheduled")
        elif growth_rate > RegulatoryThresholds.ASME_ACCEPTABLE_GROWTH:
            action = self._max_severity(action, "Monitor")

        # Add context factors to basis
        if anomaly.is_hca:
            basis += " + HCA"
        if (
            anomaly.distance_to_nearest_weld_ft is not None
            and anomaly.distance_to_nearest_weld_ft < 3.0
        ):
            basis += " + Weld Proximity"
        if anomaly.is_cluster:
            basis += " + ASME B31G Interaction"

        # Override action if risk level is CRITICAL
        if risk_level == "CRITICAL":
            action = "Immediate"

        return RegulatoryRiskScore(
            anomaly_id=anomaly.id,
            risk_score=total_score,
            risk_level=risk_level,
            depth_contribution=depth_points,
            growth_contribution=growth_points,
            context_contribution=context_points,
            cfr_classification=cfr_classification,
            cfr_reference=cfr_reference,
            asme_classification=asme_classification,
            asme_reference=asme_reference,
            action_required=action,
            regulatory_basis=basis,
        )
