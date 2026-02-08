"""
API Request Models
==================

Pydantic models for API request bodies.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ThreeWayAnalysisRequest(BaseModel):
    """Request to run three-way analysis."""
    data_2007_path: str = Field(..., description="Path to 2007 CSV data file")
    data_2015_path: str = Field(..., description="Path to 2015 CSV data file")
    data_2022_path: str = Field(..., description="Path to 2022 CSV data file")
    date_2007: Optional[str] = Field(None, description="Inspection date 2007 (ISO format)")
    date_2015: Optional[str] = Field(None, description="Inspection date 2015 (ISO format)")
    date_2022: Optional[str] = Field(None, description="Inspection date 2022 (ISO format)")
    top_n_explain: int = Field(10, ge=1, le=50, description="Number of top chains to explain with AI")
    use_agents: bool = Field(True, description="Whether to use AI agents for explanations")
    confidence_threshold: float = Field(0.6, ge=0.0, le=1.0, description="Minimum match confidence")


class MatchAnomaliesRequest(BaseModel):
    """Request to match anomalies between two runs."""
    run1_path: str = Field(..., description="Path to run 1 CSV data")
    run2_path: str = Field(..., description="Path to run 2 CSV data")
    run1_id: str = Field(..., description="Identifier for run 1")
    run2_id: str = Field(..., description="Identifier for run 2")
    run1_date: Optional[str] = Field(None, description="Inspection date for run 1")
    run2_date: Optional[str] = Field(None, description="Inspection date for run 2")
    confidence_threshold: float = Field(0.6, ge=0.0, le=1.0)
    distance_sigma: float = Field(5.0, gt=0)
    clock_sigma: float = Field(1.0, gt=0)


class GrowthCalculationRequest(BaseModel):
    """Request to calculate growth rates."""
    run1_path: str = Field(..., description="Path to run 1 CSV data")
    run2_path: str = Field(..., description="Path to run 2 CSV data")
    run1_id: str = Field(..., description="Identifier for run 1")
    run2_id: str = Field(..., description="Identifier for run 2")
    run1_date: Optional[str] = Field(None, description="Inspection date for run 1")
    run2_date: Optional[str] = Field(None, description="Inspection date for run 2")
    time_interval_years: Optional[float] = Field(None, gt=0, description="Override time interval")


class ExplainChainRequest(BaseModel):
    """Request to explain a chain using AI agents."""
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
    match_confidence_07_15: float = 0.8
    match_confidence_15_22: float = 0.8
    risk_score: float = 0.5


class ExplainMatchRequest(BaseModel):
    """Request to explain a single match using AI agents."""
    anomaly1: dict = Field(..., description="First anomaly data (from earlier run)")
    anomaly2: dict = Field(..., description="Second anomaly data (from later run)")
    match_result: dict = Field(..., description="Match result with similarity scores")


class WebhookAnalyzeRequest(BaseModel):
    """Webhook request to trigger analysis."""
    data_2007_path: Optional[str] = Field(None, description="Path to 2007 data")
    data_2015_path: Optional[str] = Field(None, description="Path to 2015 data")
    data_2022_path: Optional[str] = Field(None, description="Path to 2022 data")
    callback_url: Optional[str] = Field(None, description="URL to POST results when complete")
    analysis_type: str = Field("three-way", description="Type of analysis to run")
    top_n_explain: int = Field(10, ge=1, le=50)
    use_agents: bool = Field(True)

