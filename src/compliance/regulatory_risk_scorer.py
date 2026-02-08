"""
Regulatory risk scoring per 49 CFR and ASME B31.8S standards.
"""

from typing import Dict, List, Optional
from enum import Enum
from src.data_models.models import AnomalyRecord, ReferencePoint


class RiskLevel(str, Enum):
    """Risk level classifications."""
    CRITICAL = "CRITICAL"      # ≥85 points
    HIGH = "HIGH"              # ≥70 points
    MODERATE = "MODERATE"      # ≥50 points
    LOW = "LOW"                # ≥30 points
    ACCEPTABLE = "ACCEPTABLE"  # <30 points


class CFRClassification(str, Enum):
    """49 CFR 192.933 action classifications."""
    IMMEDIATE_ACTION = "IMMEDIATE_ACTION"      # >80% depth or <1.1 MAOP
    SCHEDULED_ACTION = "SCHEDULED_ACTION"      # 50-80% depth
    MONITOR = "MONITOR"                        # <50% depth
    

class ASMEGrowthClass(str, Enum):
    """ASME B31.8S growth rate classifications."""
    HIGH_RISK = "HIGH_RISK"          # >5% per year
    MODERATE_RISK = "MODERATE_RISK"  # 2-5% per year
    LOW_RISK = "LOW_RISK"            # 0.5-2% per year
    ACCEPTABLE = "ACCEPTABLE"        # ≤0.5% per year


class RegulatoryRiskScorer:
    """
    Calculate regulatory risk scores per federal standards.
    
    Implements:
    - 49 CFR Parts 192 & 195 (Federal Pipeline Safety)
    - ASME B31.8S (Gas Pipeline Safety Management)
    
    Risk Score Components:
    - Depth: 0-50 points (based on % wall thickness)
    - Growth Rate: 0-30 points (based on pp/year)
    - Location: 0-20 points (HCA, proximity to welds, coating)
    
    Total: 0-100 points
    """
    
    def __init__(self):
        """Initialize regulatory risk scorer."""
        pass
    
    def calculate_depth_points(self, depth_pct: float) -> float:
        """
        Calculate depth risk points.
        
        Thresholds per 49 CFR 192.933:
        - <30%: 10 points (low risk)
        - 30-49%: 20 points (moderate)
        - 50-79%: 35 points (high)
        - ≥80%: 50 points (critical - immediate action)
        
        Args:
            depth_pct: Depth as percentage of wall thickness
        
        Returns:
            Risk points (0-50)
        """
        if depth_pct >= 80.0:
            return 50.0
        elif depth_pct >= 50.0:
            return 35.0
        elif depth_pct >= 30.0:
            return 20.0
        else:
            return 10.0
    
    def calculate_growth_rate_points(self, growth_rate: float) -> float:
        """
        Calculate growth rate risk points.
        
        Thresholds per ASME B31.8S:
        - ≤0.5 pp/yr: 5 points (acceptable)
        - 0.5-2 pp/yr: 10 points (low risk)
        - 2-5 pp/yr: 20 points (moderate risk)
        - >5 pp/yr: 30 points (high risk)
        
        Args:
            growth_rate: Growth rate in percentage points per year
        
        Returns:
            Risk points (0-30)
        """
        abs_growth = abs(growth_rate)
        
        if abs_growth > 5.0:
            return 30.0
        elif abs_growth > 2.0:
            return 20.0
        elif abs_growth > 0.5:
            return 10.0
        else:
            return 5.0
    
    def calculate_location_points(
        self,
        anomaly: AnomalyRecord,
        reference_points: List[ReferencePoint],
        is_hca: bool = False,
        coating_condition: str = "good"
    ) -> float:
        """
        Calculate location risk points.
        
        Factors:
        - HCA (High Consequence Area): +10 points
        - Proximity to girth welds: +5 points if <3 feet
        - Coating condition: +5 points if poor
        
        Args:
            anomaly: Anomaly record
            reference_points: List of reference points
            is_hca: Whether in High Consequence Area
            coating_condition: "good", "fair", or "poor"
        
        Returns:
            Risk points (0-20)
        """
        points = 0.0
        
        # HCA factor
        if is_hca:
            points += 10.0
        
        # Proximity to girth welds
        if reference_points:
            distances = [
                abs(anomaly.corrected_distance - ref.corrected_distance)
                for ref in reference_points
                if ref.feature_type in ['girth_weld', 'weld']
            ]
            if distances and min(distances) < 3.0:
                points += 5.0
        
        # Coating condition
        if coating_condition.lower() == "poor":
            points += 5.0
        
        return points
    
    def calculate_total_risk_score(
        self,
        depth_pct: float,
        growth_rate: float,
        location_points: float
    ) -> float:
        """
        Calculate total regulatory risk score.
        
        Args:
            depth_pct: Depth percentage
            growth_rate: Growth rate in pp/year
            location_points: Location risk points
        
        Returns:
            Total risk score (0-100)
        """
        depth_points = self.calculate_depth_points(depth_pct)
        growth_points = self.calculate_growth_rate_points(growth_rate)
        
        total = depth_points + growth_points + location_points
        return min(total, 100.0)  # Cap at 100
    
    def classify_risk_level(self, risk_score: float) -> RiskLevel:
        """
        Classify risk level based on total score.
        
        Thresholds:
        - ≥85: CRITICAL (immediate action)
        - ≥70: HIGH (scheduled action within 180 days)
        - ≥50: MODERATE (scheduled action within 1 year)
        - ≥30: LOW (monitor)
        - <30: ACCEPTABLE (routine inspection)
        
        Args:
            risk_score: Total risk score
        
        Returns:
            Risk level classification
        """
        if risk_score >= 85.0:
            return RiskLevel.CRITICAL
        elif risk_score >= 70.0:
            return RiskLevel.HIGH
        elif risk_score >= 50.0:
            return RiskLevel.MODERATE
        elif risk_score >= 30.0:
            return RiskLevel.LOW
        else:
            return RiskLevel.ACCEPTABLE
    
    def classify_cfr_action(
        self,
        depth_pct: float,
        maop_ratio: Optional[float] = None
    ) -> CFRClassification:
        """
        Classify required action per 49 CFR 192.933.
        
        Immediate action required if:
        - Depth >80% of wall thickness
        - Predicted failure pressure <1.1 × MAOP
        
        Args:
            depth_pct: Depth percentage
            maop_ratio: Predicted failure pressure / MAOP (optional)
        
        Returns:
            CFR action classification
        """
        # Immediate action criteria
        if depth_pct > 80.0:
            return CFRClassification.IMMEDIATE_ACTION
        
        if maop_ratio is not None and maop_ratio < 1.1:
            return CFRClassification.IMMEDIATE_ACTION
        
        # Scheduled action criteria
        if depth_pct >= 50.0:
            return CFRClassification.SCHEDULED_ACTION
        
        # Monitor
        return CFRClassification.MONITOR
    
    def classify_asme_growth_rate(self, growth_rate: float) -> ASMEGrowthClass:
        """
        Classify growth rate per ASME B31.8S.
        
        Classifications:
        - >5 pp/yr: HIGH_RISK
        - 2-5 pp/yr: MODERATE_RISK
        - 0.5-2 pp/yr: LOW_RISK
        - ≤0.5 pp/yr: ACCEPTABLE
        
        Args:
            growth_rate: Growth rate in percentage points per year
        
        Returns:
            ASME growth rate classification
        """
        abs_growth = abs(growth_rate)
        
        if abs_growth > 5.0:
            return ASMEGrowthClass.HIGH_RISK
        elif abs_growth > 2.0:
            return ASMEGrowthClass.MODERATE_RISK
        elif abs_growth > 0.5:
            return ASMEGrowthClass.LOW_RISK
        else:
            return ASMEGrowthClass.ACCEPTABLE
    
    def score_anomaly(
        self,
        anomaly: AnomalyRecord,
        growth_rate: float,
        reference_points: List[ReferencePoint],
        is_hca: bool = False,
        coating_condition: str = "good",
        maop_ratio: Optional[float] = None
    ) -> Dict:
        """
        Complete regulatory risk assessment for an anomaly.
        
        Args:
            anomaly: Anomaly record
            growth_rate: Growth rate in pp/year
            reference_points: List of reference points
            is_hca: Whether in High Consequence Area
            coating_condition: Coating condition
            maop_ratio: Predicted failure pressure / MAOP
        
        Returns:
            Dictionary with complete risk assessment
        """
        # Calculate component scores
        depth_points = self.calculate_depth_points(anomaly.depth_pct)
        growth_points = self.calculate_growth_rate_points(growth_rate)
        location_points = self.calculate_location_points(
            anomaly, reference_points, is_hca, coating_condition
        )
        
        # Total score
        total_score = self.calculate_total_risk_score(
            anomaly.depth_pct, growth_rate, location_points
        )
        
        # Classifications
        risk_level = self.classify_risk_level(total_score)
        cfr_classification = self.classify_cfr_action(anomaly.depth_pct, maop_ratio)
        asme_classification = self.classify_asme_growth_rate(growth_rate)
        
        return {
            'anomaly_id': anomaly.id,
            'depth_pct': anomaly.depth_pct,
            'growth_rate': growth_rate,
            'depth_points': depth_points,
            'growth_points': growth_points,
            'location_points': location_points,
            'total_risk_score': total_score,
            'risk_level': risk_level.value,
            'cfr_classification': cfr_classification.value,
            'asme_growth_classification': asme_classification.value,
            'is_hca': is_hca,
            'coating_condition': coating_condition
        }
    
    def rank_by_regulatory_risk(
        self,
        assessments: List[Dict]
    ) -> List[Dict]:
        """
        Rank anomalies by regulatory risk score.
        
        Args:
            assessments: List of risk assessments
        
        Returns:
            Sorted list (highest risk first)
        """
        return sorted(
            assessments,
            key=lambda x: x['total_risk_score'],
            reverse=True
        )
    
    def get_immediate_action_items(
        self,
        assessments: List[Dict]
    ) -> List[Dict]:
        """
        Filter anomalies requiring immediate action.
        
        Args:
            assessments: List of risk assessments
        
        Returns:
            List of immediate action items
        """
        return [
            a for a in assessments
            if a['cfr_classification'] == CFRClassification.IMMEDIATE_ACTION.value
        ]

