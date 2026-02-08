"""
Analysis Router
===============

Endpoints for running and retrieving three-way analysis.
"""

import uuid
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from src.api.schemas.requests import ThreeWayAnalysisRequest
from src.api.schemas.responses import (
    ThreeWayAnalysisResponse,
    AnalysisStatusResponse,
    ChainResponse,
    ChainExplanationResponse,
)

router = APIRouter()


def _run_analysis_background(analysis_id: str, request: ThreeWayAnalysisRequest, store: dict):
    """Run three-way analysis in background."""
    try:
        store[analysis_id]["status"] = "RUNNING"
        store[analysis_id]["progress_pct"] = 10.0

        from src.analysis.three_way_analyzer import ThreeWayAnalyzer

        date_2007 = datetime.fromisoformat(request.date_2007) if request.date_2007 else None
        date_2015 = datetime.fromisoformat(request.date_2015) if request.date_2015 else None
        date_2022 = datetime.fromisoformat(request.date_2022) if request.date_2022 else None

        analyzer = ThreeWayAnalyzer(
            confidence_threshold=request.confidence_threshold,
            use_agents=request.use_agents,
        )

        result = analyzer.run_full_analysis(
            data_2007_path=request.data_2007_path,
            data_2015_path=request.data_2015_path,
            data_2022_path=request.data_2022_path,
            date_2007=date_2007,
            date_2015=date_2015,
            date_2022=date_2022,
            top_n_explain=request.top_n_explain,
            output_dir=f"output/api_analysis_{analysis_id}",
        )

        # Build response
        chains = [
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
            for c in result.chains
        ]

        explanations = [
            ChainExplanationResponse(
                chain_id=e.chain_id,
                trend_classification=e.trend_classification,
                urgency_level=e.urgency_level,
                lifecycle_narrative=e.lifecycle_narrative,
                trend_analysis=e.trend_analysis,
                projection_analysis=e.projection_analysis,
                recommendation=e.recommendation,
                concerns=e.concerns,
            )
            for e in result.explanations
        ]

        response = ThreeWayAnalysisResponse(
            analysis_id=analysis_id,
            status="COMPLETE",
            timestamp=result.timestamp.isoformat(),
            total_anomalies_2007=result.total_anomalies_2007,
            total_anomalies_2015=result.total_anomalies_2015,
            total_anomalies_2022=result.total_anomalies_2022,
            matched_07_15=result.matched_07_15,
            matched_15_22=result.matched_15_22,
            total_chains=result.total_chains,
            accelerating_count=result.accelerating_count,
            stable_count=result.stable_count,
            decelerating_count=result.decelerating_count,
            immediate_action_count=result.immediate_action_count,
            avg_growth_rate_07_15=result.avg_growth_rate_07_15,
            avg_growth_rate_15_22=result.avg_growth_rate_15_22,
            dtw_applied_07_15=result.dtw_applied_07_15,
            dtw_applied_15_22=result.dtw_applied_15_22,
            dtw_fallback_reason_07_15=result.dtw_fallback_reason_07_15,
            dtw_fallback_reason_15_22=result.dtw_fallback_reason_15_22,
            chains=chains,
            explanations=explanations,
        )

        store[analysis_id]["status"] = "COMPLETE"
        store[analysis_id]["progress_pct"] = 100.0
        store[analysis_id]["completed_at"] = datetime.now()
        store[analysis_id]["result"] = response

    except Exception as e:
        store[analysis_id]["status"] = "FAILED"
        store[analysis_id]["message"] = str(e)


@router.post("/analyze/three-way", response_model=AnalysisStatusResponse)
async def start_three_way_analysis(
    request: ThreeWayAnalysisRequest,
    background_tasks: BackgroundTasks,
    req: Request,
):
    """
    Start a three-way analysis (2007 → 2015 → 2022).

    This is an async operation. Returns an analysis_id that can be polled
    via GET /api/analysis/{analysis_id} for status and results.
    """
    analysis_id = str(uuid.uuid4())[:8]
    store = req.app.state.analysis_store

    store[analysis_id] = {
        "status": "PENDING",
        "progress_pct": 0.0,
        "message": "Analysis queued",
        "created_at": datetime.now(),
        "completed_at": None,
        "result": None,
    }

    background_tasks.add_task(
        _run_analysis_background, analysis_id, request, store
    )

    return AnalysisStatusResponse(
        analysis_id=analysis_id,
        status="PENDING",
        progress_pct=0.0,
        message="Analysis queued. Poll GET /api/analysis/{analysis_id} for status.",
        created_at=store[analysis_id]["created_at"],
    )


@router.get("/analysis/{analysis_id}")
async def get_analysis_status(analysis_id: str, req: Request):
    """
    Get analysis status and results.

    Returns status while running, full results when complete.
    """
    store = req.app.state.analysis_store

    if analysis_id not in store:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

    entry = store[analysis_id]

    if entry["status"] == "COMPLETE" and entry.get("result"):
        return entry["result"]

    return AnalysisStatusResponse(
        analysis_id=analysis_id,
        status=entry["status"],
        progress_pct=entry["progress_pct"],
        message=entry.get("message", ""),
        created_at=entry["created_at"],
        completed_at=entry.get("completed_at"),
    )

