"""
API Response Models
===================

Pydantic models for all API responses (JSON serializable).
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


# ─── Analysis Responses ────────────────────────────────────────────────

class AnalysisStatusResponse(BaseModel):
    """Status of an ongoing or completed analysis."""
    analysis_id: str
    status: Literal["PENDING", "RUNNING", "COMPLETE", "FAILED"]
    progress_pct: float = 0.0
    message: str = ""
    created_at: datetime
    completed_at: Optional[datetime] = None


class ChainResponse(BaseModel):
    """Single anomaly chain with growth data."""
    chain_id: str
    anomaly_2007_id: str
    anomaly_2015_id: str
    anomaly_2022_id: str
    depth_2007: float
    depth_2015: float
    depth_2022: float
    growth_rate_07_15: float
    growth_rate_15_22: float
    acceleration: float
    is_accelerating: bool
    risk_score: float
    years_to_80pct: Optional[float] = None
    match_confidence_07_15: float
    match_confidence_15_22: float


class ChainExplanationResponse(BaseModel):
    """AI-generated explanation for a chain."""
    chain_id: str
    trend_classification: str
    urgency_level: str
    lifecycle_narrative: str
    trend_analysis: str
    projection_analysis: str
    recommendation: str
    concerns: List[str] = Field(default_factory=list)


class ChainDetailResponse(BaseModel):
    """Single chain with full detail including AI explanation."""
    chain: ChainResponse
    explanation: Optional[ChainExplanationResponse] = None


class ChainsListResponse(BaseModel):
    """List of chains with pagination info."""
    chains: List[ChainResponse]
    total: int
    page: int = 1
    per_page: int = 50


class ThreeWayAnalysisResponse(BaseModel):
    """Complete three-way analysis result."""
    analysis_id: str
    status: str
    timestamp: str
    total_anomalies_2007: int
    total_anomalies_2015: int
    total_anomalies_2022: int
    matched_07_15: int
    matched_15_22: int
    total_chains: int
    accelerating_count: int
    stable_count: int
    decelerating_count: int
    immediate_action_count: int
    avg_growth_rate_07_15: float
    avg_growth_rate_15_22: float
    chains: List[ChainResponse] = Field(default_factory=list)
    explanations: List[ChainExplanationResponse] = Field(default_factory=list)


# ─── Matching Responses ────────────────────────────────────────────────

class MatchResponse(BaseModel):
    """A single anomaly match."""
    match_id: str
    anomaly1_id: str
    anomaly2_id: str
    similarity_score: float
    confidence: str
    distance_similarity: float
    clock_similarity: float
    type_similarity: float
    depth_similarity: float


class MatchingResultResponse(BaseModel):
    """Result of matching two runs."""
    run1_id: str
    run2_id: str
    total_run1: int
    total_run2: int
    matched: int
    match_rate: float
    high_confidence: int
    medium_confidence: int
    low_confidence: int
    matches: List[MatchResponse] = Field(default_factory=list)
    new_anomalies: int = 0
    repaired_anomalies: int = 0


# ─── Growth Responses ─────────────────────────────────────────────────

class GrowthMetricsResponse(BaseModel):
    """Growth metrics for a single match."""
    match_id: str
    depth_growth_rate: float
    length_growth_rate: float
    width_growth_rate: float
    is_rapid_growth: bool
    risk_score: float


class GrowthCalculationResponse(BaseModel):
    """Result of growth calculation."""
    total_matches: int
    rapid_growth_count: int
    rapid_growth_percentage: float
    avg_depth_growth: float
    max_depth_growth: float
    metrics: List[GrowthMetricsResponse] = Field(default_factory=list)


class TrajectoryPoint(BaseModel):
    """A single point in a growth trajectory."""
    year: int
    depth_pct: float
    growth_rate: Optional[float] = None


class GrowthTrajectoryResponse(BaseModel):
    """Growth trajectory for a single chain."""
    chain_id: str
    points: List[TrajectoryPoint]
    acceleration: float
    is_accelerating: bool
    projected_80pct_year: Optional[int] = None


class TrajectoriesResponse(BaseModel):
    """All growth trajectories for visualization."""
    trajectories: List[GrowthTrajectoryResponse]
    total: int


# ─── Anomaly Responses ────────────────────────────────────────────────

class AnomalyResponse(BaseModel):
    """A single anomaly record."""
    id: str
    run_id: str
    distance: float
    clock_position: float
    depth_pct: float
    length: float
    width: float
    feature_type: str


class AnomaliesListResponse(BaseModel):
    """List of anomalies for a run."""
    run_id: str
    anomalies: List[AnomalyResponse]
    total: int


# ─── Explain Responses ────────────────────────────────────────────────

class MatchExplanationResponse(BaseModel):
    """AI explanation for a single match."""
    match_id: str
    confidence: str
    explanation: str
    recommendation: str
    concerns: List[str] = Field(default_factory=list)
    similarity_score: float


# ─── Report Responses ─────────────────────────────────────────────────

class ExecutiveSummaryResponse(BaseModel):
    """Executive summary for dashboard."""
    total_anomalies: Dict[str, int]
    matching_stats: Dict[str, Any]
    growth_summary: Dict[str, Any]
    risk_distribution: Dict[str, int]
    trend_breakdown: Dict[str, int]
    immediate_action_count: int
    cost_savings_estimate: Dict[str, float]
    time_savings_hours: float


class RiskRankingItem(BaseModel):
    """Single item in risk ranking."""
    rank: int
    anomaly_id: str
    chain_id: Optional[str] = None
    risk_score: float
    depth_pct: float
    growth_rate: float
    urgency: str
    years_to_critical: Optional[float] = None


class RiskRankingResponse(BaseModel):
    """Risk ranking of anomalies."""
    rankings: List[RiskRankingItem]
    total: int
    critical_count: int
    high_count: int


# ─── Webhook Responses ────────────────────────────────────────────────

class WebhookResponse(BaseModel):
    """Response from webhook endpoints."""
    success: bool
    message: str
    analysis_id: Optional[str] = None
    status_url: Optional[str] = None


class UploadResponse(BaseModel):
    """Response from file upload."""
    success: bool
    message: str
    run_id: str
    anomaly_count: int
    reference_point_count: int


# ─── Health Check ─────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """API health check response."""
    status: str = "healthy"
    version: str = "0.1.0"
    timestamp: str
    agents_available: bool
    datasets_available: List[str] = Field(default_factory=list)

