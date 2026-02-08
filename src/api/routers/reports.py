"""
Reports Router
==============

Endpoints for executive summaries and risk rankings.
"""

from fastapi import APIRouter, HTTPException, Request

from src.api.schemas.responses import (
    ExecutiveSummaryResponse,
    RiskRankingResponse,
    RiskRankingItem,
)

router = APIRouter()


@router.get("/reports/summary", response_model=ExecutiveSummaryResponse)
async def get_executive_summary(req: Request):
    """
    Get executive summary for dashboard display.

    Returns aggregated metrics, risk distribution, trend breakdown,
    and business impact estimates.
    """
    store = req.app.state.analysis_store

    # Find latest completed analysis
    latest_result = None
    for aid, entry in store.items():
        if entry["status"] == "COMPLETE" and entry.get("result"):
            latest_result = entry["result"]

    if not latest_result:
        raise HTTPException(
            status_code=404,
            detail="No completed analysis found. Run POST /api/analyze/three-way first.",
        )

    r = latest_result

    # Risk distribution
    critical = sum(1 for c in r.chains if c.risk_score >= 0.7)
    high = sum(1 for c in r.chains if 0.5 <= c.risk_score < 0.7)
    moderate = sum(1 for c in r.chains if 0.3 <= c.risk_score < 0.5)
    low = sum(1 for c in r.chains if c.risk_score < 0.3)

    # Cost savings estimate (same formula as demo)
    traditional_digs = 50
    smart_digs = critical + min(
        sum(1 for c in r.chains if c.growth_rate_15_22 > 5 and c.depth_2022 > 70), 10
    )
    savings_low = (traditional_digs - smart_digs) * 50_000
    savings_high = (traditional_digs - smart_digs) * 500_000

    return ExecutiveSummaryResponse(
        total_anomalies={
            "2007": r.total_anomalies_2007,
            "2015": r.total_anomalies_2015,
            "2022": r.total_anomalies_2022,
        },
        matching_stats={
            "matched_07_15": r.matched_07_15,
            "matched_15_22": r.matched_15_22,
            "total_chains": r.total_chains,
        },
        growth_summary={
            "avg_growth_07_15": r.avg_growth_rate_07_15,
            "avg_growth_15_22": r.avg_growth_rate_15_22,
        },
        risk_distribution={
            "critical": critical,
            "high": high,
            "moderate": moderate,
            "low": low,
        },
        trend_breakdown={
            "accelerating": r.accelerating_count,
            "stable": r.stable_count,
            "decelerating": r.decelerating_count,
        },
        immediate_action_count=r.immediate_action_count,
        cost_savings_estimate={
            "low_estimate": savings_low / 1_000_000,
            "high_estimate": savings_high / 1_000_000,
            "traditional_digs": traditional_digs,
            "smart_digs": smart_digs,
        },
        time_savings_hours=158.0,  # 160 manual - 2 automated
    )


@router.get("/reports/risk-ranking", response_model=RiskRankingResponse)
async def get_risk_ranking(req: Request, limit: int = 50):
    """
    Get ranked anomaly chains by risk score (highest first).

    Used for priority list in frontend dashboard.
    """
    store = req.app.state.analysis_store

    latest_result = None
    for aid, entry in store.items():
        if entry["status"] == "COMPLETE" and entry.get("result"):
            latest_result = entry["result"]

    if not latest_result:
        raise HTTPException(
            status_code=404,
            detail="No completed analysis found. Run POST /api/analyze/three-way first.",
        )

    # Chains are already sorted by risk score in the analyzer
    rankings = []
    for rank, chain in enumerate(latest_result.chains[:limit], 1):
        # Determine urgency
        from src.agents.chain_storyteller import ProjectionAgent

        years = chain.years_to_80pct
        urgency = ProjectionAgent.assess_urgency(years, chain.depth_2022)

        rankings.append(
            RiskRankingItem(
                rank=rank,
                anomaly_id=chain.anomaly_2022_id,
                chain_id=chain.chain_id,
                risk_score=chain.risk_score,
                depth_pct=chain.depth_2022,
                growth_rate=chain.growth_rate_15_22,
                urgency=urgency,
                years_to_critical=years,
            )
        )

    critical_count = sum(1 for c in latest_result.chains if c.risk_score >= 0.7)
    high_count = sum(1 for c in latest_result.chains if 0.5 <= c.risk_score < 0.7)

    return RiskRankingResponse(
        rankings=rankings,
        total=len(latest_result.chains),
        critical_count=critical_count,
        high_count=high_count,
    )

