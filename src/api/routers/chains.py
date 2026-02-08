"""
Chains Router
=============

Endpoints for retrieving anomaly chains and their details.
"""

from fastapi import APIRouter, HTTPException, Request, Query

from src.api.schemas.responses import (
    ChainsListResponse,
    ChainResponse,
    ChainDetailResponse,
    ChainExplanationResponse,
)

router = APIRouter()


@router.get("/chains", response_model=ChainsListResponse)
async def get_chains(
    req: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    sort_by: str = Query("risk_score", pattern="^(risk_score|acceleration|depth_2022|growth_rate_15_22)$"),
    min_risk: float = Query(0.0, ge=0.0, le=1.0),
    accelerating_only: bool = Query(False),
):
    """
    Get all anomaly chains with growth data.

    Supports pagination, filtering, and sorting.
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

    # Filter chains
    all_chains = latest_result.chains
    filtered = [c for c in all_chains if c.risk_score >= min_risk]

    if accelerating_only:
        filtered = [c for c in filtered if c.is_accelerating]

    # Sort
    sort_map = {
        "risk_score": lambda c: c.risk_score,
        "acceleration": lambda c: c.acceleration,
        "depth_2022": lambda c: c.depth_2022,
        "growth_rate_15_22": lambda c: c.growth_rate_15_22,
    }
    filtered.sort(key=sort_map.get(sort_by, sort_map["risk_score"]), reverse=True)

    # Paginate
    total = len(filtered)
    start = (page - 1) * per_page
    end = start + per_page
    page_chains = filtered[start:end]

    chains_response = [
        ChainResponse(
            chain_id=c.chain_id,
            anomaly_2007_id=c.anomaly_2007_id,
            anomaly_2015_id=c.anomaly_2015_id,
            anomaly_2022_id=c.anomaly_2022_id,
            depth_2007=c.depth_2007,
            depth_2015=c.depth_2015,
            depth_2022=c.depth_2022,
            growth_rate_07_15=c.growth_rate_07_15,
            growth_rate_15_22=c.growth_rate_15_22,
            acceleration=c.acceleration,
            is_accelerating=c.is_accelerating,
            risk_score=c.risk_score,
            years_to_80pct=c.years_to_80pct,
            match_confidence_07_15=c.match_confidence_07_15,
            match_confidence_15_22=c.match_confidence_15_22,
        )
        for c in page_chains
    ]

    return ChainsListResponse(
        chains=chains_response,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/chains/{chain_id}", response_model=ChainDetailResponse)
async def get_chain_detail(chain_id: str, req: Request):
    """
    Get a single chain with full detail and AI explanation.
    """
    store = req.app.state.analysis_store

    latest_result = None
    for aid, entry in store.items():
        if entry["status"] == "COMPLETE" and entry.get("result"):
            latest_result = entry["result"]

    if not latest_result:
        raise HTTPException(
            status_code=404,
            detail="No completed analysis found.",
        )

    # Find chain
    chain = None
    for c in latest_result.chains:
        if c.chain_id == chain_id:
            chain = c
            break

    if not chain:
        raise HTTPException(status_code=404, detail=f"Chain '{chain_id}' not found")

    chain_resp = ChainResponse(
        chain_id=chain.chain_id,
        anomaly_2007_id=chain.anomaly_2007_id,
        anomaly_2015_id=chain.anomaly_2015_id,
        anomaly_2022_id=chain.anomaly_2022_id,
        depth_2007=chain.depth_2007,
        depth_2015=chain.depth_2015,
        depth_2022=chain.depth_2022,
        growth_rate_07_15=chain.growth_rate_07_15,
        growth_rate_15_22=chain.growth_rate_15_22,
        acceleration=chain.acceleration,
        is_accelerating=chain.is_accelerating,
        risk_score=chain.risk_score,
        years_to_80pct=chain.years_to_80pct,
        match_confidence_07_15=chain.match_confidence_07_15,
        match_confidence_15_22=chain.match_confidence_15_22,
    )

    # Find explanation if available
    explanation = None
    for e in latest_result.explanations:
        if e.chain_id == chain_id:
            explanation = ChainExplanationResponse(
                chain_id=e.chain_id,
                trend_classification=e.trend_classification,
                urgency_level=e.urgency_level,
                lifecycle_narrative=e.lifecycle_narrative,
                trend_analysis=e.trend_analysis,
                projection_analysis=e.projection_analysis,
                recommendation=e.recommendation,
                concerns=e.concerns,
            )
            break

    return ChainDetailResponse(chain=chain_resp, explanation=explanation)

