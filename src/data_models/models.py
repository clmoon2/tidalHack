"""
Pydantic data models for ILI system.

This module defines the core data structures with validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime


class AnomalyRecord(BaseModel):
    """Single anomaly from ILI run"""

    id: str = Field(..., description="Unique identifier")
    run_id: str = Field(..., description="Inspection run identifier")
    distance: float = Field(..., ge=0, description="Odometer reading in feet")
    clock_position: float = Field(..., ge=1, le=12, description="Circumferential position")
    depth_pct: float = Field(
        ..., ge=0, le=100, description="Depth as percentage of wall thickness"
    )
    length: float = Field(..., gt=0, description="Axial length in inches")
    width: float = Field(..., gt=0, description="Circumferential width in inches")
    feature_type: Literal["external_corrosion", "internal_corrosion", "dent", "crack", "other"]
    coating_type: Optional[str] = None
    inspection_date: datetime

    @field_validator("clock_position")
    @classmethod
    def validate_clock(cls, v: float) -> float:
        if not (1 <= v <= 12):
            raise ValueError("Clock position must be between 1 and 12")
        return v


class ReferencePoint(BaseModel):
    """Reference point for alignment"""

    id: str
    run_id: str
    distance: float = Field(..., ge=0)
    point_type: Literal["girth_weld", "valve", "tee", "other"]
    description: Optional[str] = None


class Match(BaseModel):
    """Matched anomaly pair"""

    id: str
    anomaly1_id: str
    anomaly2_id: str
    similarity_score: float = Field(..., ge=0, le=1)
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
    distance_similarity: float
    clock_similarity: float
    type_similarity: float
    depth_similarity: float
    length_similarity: float
    width_similarity: float

    @field_validator("confidence", mode="before")
    @classmethod
    def set_confidence(cls, v: Any, info: Any) -> str:
        # Access similarity_score from the data being validated
        data = info.data
        score = data.get("similarity_score", 0)
        if score >= 0.8:
            return "HIGH"
        elif score >= 0.6:
            return "MEDIUM"
        else:
            return "LOW"


class GrowthMetrics(BaseModel):
    """Growth analysis for matched pair"""

    match_id: str
    time_interval_years: float
    depth_growth_rate: float = Field(..., description="Percentage points per year")
    length_growth_rate: float = Field(..., description="Inches per year")
    width_growth_rate: float = Field(..., description="Inches per year")
    is_rapid_growth: bool = False
    risk_score: float = Field(..., ge=0, le=1)

    @field_validator("is_rapid_growth", mode="before")
    @classmethod
    def check_rapid_growth(cls, v: Any, info: Any) -> bool:
        data = info.data
        return data.get("depth_growth_rate", 0) > 5.0


class Prediction(BaseModel):
    """ML prediction for future depth"""

    anomaly_id: str
    current_depth_pct: float
    predicted_depth_pct: float
    years_ahead: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    model_confidence: Literal["HIGH", "MEDIUM", "LOW"]
    top_features: List[tuple[str, float]]  # (feature_name, shap_value)


class AlignmentResult(BaseModel):
    """Result of DTW alignment"""

    run1_id: str
    run2_id: str
    matched_points: List[tuple[str, str]]  # (ref_point1_id, ref_point2_id)
    match_rate: float = Field(..., ge=0, le=100)
    rmse: float = Field(..., ge=0)
    correction_function_params: Dict[str, Any]

    @field_validator("match_rate")
    @classmethod
    def validate_match_rate(cls, v: float) -> float:
        if v < 95.0:
            raise ValueError("Match rate below 95% threshold")
        return v

    @field_validator("rmse")
    @classmethod
    def validate_rmse(cls, v: float) -> float:
        if v > 10.0:
            raise ValueError("RMSE exceeds 10 feet threshold")
        return v


class ValidationResult(BaseModel):
    """Result of data validation"""

    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    record_count: int
    valid_count: int
    invalid_count: int


# Regulatory Compliance Models

class RegulatoryRiskScore(BaseModel):
    """Regulatory-compliant risk score per 49 CFR and ASME B31.8S"""

    anomaly_id: str
    risk_score: int = Field(..., ge=0, le=100, description="Total risk score 0-100")
    risk_level: Literal["CRITICAL", "HIGH", "MODERATE", "LOW", "ACCEPTABLE"]
    depth_contribution: int = Field(..., ge=0, le=50)
    growth_contribution: int = Field(..., ge=0, le=30)
    context_contribution: int = Field(..., ge=0, le=20)
    cfr_classification: Literal["IMMEDIATE_ACTION", "SCHEDULED_ACTION", "MONITORING"]
    cfr_reference: str
    asme_classification: Literal["ACCEPTABLE", "ACCEPTABLE_MONITOR", "MODERATE_RISK", "HIGH_RISK"]
    asme_reference: str
    action_required: Literal["Immediate", "Scheduled", "Monitor", "Standard"]
    regulatory_basis: str

    @field_validator("risk_level", mode="before")
    @classmethod
    def set_risk_level(cls, v: Any, info: Any) -> str:
        data = info.data
        score = data.get("risk_score", 0)
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


class InspectionInterval(BaseModel):
    """Inspection interval calculation result"""

    anomaly_id: str
    recommended_years: float = Field(..., gt=0, description="Recommended inspection interval in years")
    years_to_critical: float = Field(..., description="Years until 80% depth threshold")
    regulatory_max_years: float = Field(..., description="Regulatory maximum interval")
    next_inspection_date: datetime
    interval_basis: Literal["GROWTH_BASED", "REGULATORY_MAXIMUM", "DEPTH_BASED"]
    basis_description: str
    regulatory_reference: str = "49 CFR 192.937 & ASME B31.8S"

    @field_validator("recommended_years")
    @classmethod
    def validate_interval(cls, v: float, info: Any) -> float:
        data = info.data
        reg_max = data.get("regulatory_max_years", 7.0)
        if v > reg_max:
            raise ValueError(f"Recommended interval {v} exceeds regulatory maximum {reg_max}")
        return v


class ComplianceReport(BaseModel):
    """Compliance report metadata"""

    report_id: str
    pipeline_segment: str
    assessment_period_start: datetime
    assessment_period_end: datetime
    generated_at: datetime
    total_anomalies: int
    immediate_action_count: int
    scheduled_action_count: int
    critical_count: int
    high_count: int
    moderate_count: int
    low_count: int
    acceptable_count: int
    highest_risk_score: int
    average_growth_rate: float
    compliance_status: Literal["COMPLIANT", "NON_COMPLIANT"]


class AnomalyWithRegulatory(AnomalyRecord):
    """Extended anomaly record with regulatory fields"""

    corrected_distance: Optional[float] = None
    is_hca: bool = False
    distance_to_nearest_weld_ft: Optional[float] = None
    is_cluster: bool = False
    coating_condition: Optional[Literal["good", "fair", "poor"]] = None
    maop_ratio: Optional[float] = None
    wall_thickness_in: Optional[float] = None
    
    # Regulatory fields
    risk_score: Optional[int] = None
    risk_level: Optional[Literal["CRITICAL", "HIGH", "MODERATE", "LOW", "ACCEPTABLE"]] = None
    cfr_classification: Optional[Literal["IMMEDIATE_ACTION", "SCHEDULED_ACTION", "MONITORING"]] = None
    asme_classification: Optional[Literal["ACCEPTABLE", "ACCEPTABLE_MONITOR", "MODERATE_RISK", "HIGH_RISK"]] = None
    action_required: Optional[Literal["Immediate", "Scheduled", "Monitor", "Standard"]] = None
    inspection_interval_years: Optional[float] = None
    next_inspection_date: Optional[datetime] = None
    
    # Growth fields
    growth_rate_pct_per_year: Optional[float] = None
    growth_rate_mils_per_year: Optional[float] = None
    
    # Compliance flags
    exceeds_cfr_192_933: bool = False  # >80% depth
    exceeds_cfr_195_452: bool = False  # 50-80% depth
    exceeds_asme_growth: bool = False  # >0.5%/year
    high_growth_flag: bool = False  # >5%/year


# Constants for regulatory thresholds
# Three-Way Analysis Models

class AnomalyChain(BaseModel):
    """A chain linking the same anomaly across 3 inspection runs (2007→2015→2022)."""

    chain_id: str = Field(..., description="Unique chain identifier")
    anomaly_2007_id: str = Field(..., description="Anomaly ID from 2007 run")
    anomaly_2015_id: str = Field(..., description="Anomaly ID from 2015 run")
    anomaly_2022_id: str = Field(..., description="Anomaly ID from 2022 run")
    match_confidence_07_15: float = Field(..., ge=0, le=1, description="Match confidence 2007→2015")
    match_confidence_15_22: float = Field(..., ge=0, le=1, description="Match confidence 2015→2022")
    depth_2007: float = Field(..., ge=0, le=100, description="Depth % in 2007")
    depth_2015: float = Field(..., ge=0, le=100, description="Depth % in 2015")
    depth_2022: float = Field(..., ge=0, le=100, description="Depth % in 2022")
    growth_rate_07_15: float = Field(..., description="Growth rate 2007→2015 (pp/year)")
    growth_rate_15_22: float = Field(..., description="Growth rate 2015→2022 (pp/year)")
    acceleration: float = Field(..., description="Change in growth rate between intervals")
    is_accelerating: bool = Field(default=False, description="Whether growth is accelerating")
    risk_score: float = Field(..., ge=0, le=1, description="Composite risk score")
    years_to_80pct: Optional[float] = Field(None, description="Projected years to 80% critical depth")

    @field_validator("is_accelerating", mode="before")
    @classmethod
    def check_acceleration(cls, v: Any, info: Any) -> bool:
        data = info.data
        return data.get("acceleration", 0) > 0.1  # > 0.1 pp/yr² considered accelerating


class ChainExplanation(BaseModel):
    """AI-generated explanation for an anomaly chain."""

    chain_id: str
    trend_classification: Literal["ACCELERATING", "STABLE", "DECELERATING"]
    urgency_level: Literal["IMMEDIATE", "NEAR_TERM", "SCHEDULED", "MONITOR"]
    lifecycle_narrative: str = Field(..., description="Full lifecycle story of the anomaly")
    trend_analysis: str = Field(..., description="Analysis of growth trend across intervals")
    projection_analysis: str = Field(..., description="Future state projection")
    recommendation: str = Field(..., description="Recommended action")
    concerns: List[str] = Field(default_factory=list)


class ThreeWayAnalysisResult(BaseModel):
    """Complete result of a three-way analysis."""

    analysis_id: str
    timestamp: datetime
    total_anomalies_2007: int
    total_anomalies_2015: int
    total_anomalies_2022: int
    matched_07_15: int
    matched_15_22: int
    total_chains: int
    chains: List[AnomalyChain] = Field(default_factory=list)
    explanations: List[ChainExplanation] = Field(default_factory=list)
    accelerating_count: int = 0
    stable_count: int = 0
    decelerating_count: int = 0
    immediate_action_count: int = 0
    avg_growth_rate_07_15: float = 0.0
    avg_growth_rate_15_22: float = 0.0
    status: Literal["PENDING", "RUNNING", "COMPLETE", "FAILED"] = "PENDING"
    error_message: Optional[str] = None


class RegulatoryThresholds:
    """Regulatory threshold constants"""
    
    # 49 CFR thresholds
    CFR_IMMEDIATE_DEPTH = 80.0  # % wall thickness
    CFR_SCHEDULED_DEPTH = 50.0  # % wall thickness
    CFR_MAOP_RATIO = 1.1
    
    # ASME B31.8S growth rate thresholds (% per year)
    ASME_ACCEPTABLE_GROWTH = 0.5
    ASME_MODERATE_GROWTH = 2.0
    ASME_HIGH_GROWTH = 5.0
    
    # Inspection intervals (years)
    HCA_MAX_INTERVAL = 5.0
    NON_HCA_MAX_INTERVAL = 7.0
    SAFETY_FACTOR = 0.5
    
    # Risk scoring points
    DEPTH_MAX_POINTS = 50
    GROWTH_MAX_POINTS = 30
    CONTEXT_MAX_POINTS = 20
    
    # Color codes
    COLOR_CRITICAL = "#DC143C"  # Red
    COLOR_HIGH = "#FF8C00"  # Orange
    COLOR_MODERATE = "#FFD700"  # Yellow
    COLOR_LOW = "#90EE90"  # Light Green
    COLOR_ACCEPTABLE = "#228B22"  # Dark Green
