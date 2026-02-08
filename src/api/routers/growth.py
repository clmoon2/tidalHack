"""
Growth Router
=============

Endpoints for growth rate calculation and trajectories.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Request

from src.api.schemas.requests import GrowthCalculationRequest
from src.api.schemas.responses import (
    GrowthCalculationResponse,
    GrowthMetricsResponse,
    TrajectoriesResponse,
    GrowthTrajectoryResponse,
    TrajectoryPoint,
)

router = APIRouter()


@router.post("/growth/calculate", response_model=GrowthCalculationResponse)
async def calculate_growth(request: GrowthCalculationRequest):
    """
    Calculate growth rates for matched anomalies between two runs.
    """
    try:
        from src.ingestion.loader import ILIDataLoader
        from src.data_models.models import AnomalyRecord
        from src.matching.matcher import HungarianMatcher
        from src.matching.similarity import SimilarityCalculator
        from src.growth.analyzer import GrowthAnalyzer

        loader = ILIDataLoader()

        date1 = datetime.fromisoformat(request.run1_date) if request.run1_date else datetime(2020, 1, 1)
        date2 = datetime.fromisoformat(request.run2_date) if request.run2_date else datetime(2022, 1, 1)

        # Determine time interval
        if request.time_interval_years:
            time_interval = request.time_interval_years
        else:
            time_interval = (date2 - date1).days / 365.25

        df1, _ = loader.load_and_process(request.run1_path, request.run1_id, date1)
        df2, _ = loader.load_and_process(request.run2_path, request.run2_id, date2)

        # Build anomaly lists
        anomalies_1, anomalies_2 = [], []
        for idx, row in df1.iterrows():
            try:
                anomalies_1.append(AnomalyRecord(
                    id=f"{request.run1_id}_{idx}", run_id=request.run1_id,
                    distance=float(row["distance"]), clock_position=float(row["clock_position"]),
                    depth_pct=float(row["depth_pct"]), length=float(row["length"]),
                    width=float(row["width"]), feature_type=row["feature_type"],
                    inspection_date=date1,
                ))
            except Exception:
                pass
        for idx, row in df2.iterrows():
            try:
                anomalies_2.append(AnomalyRecord(
                    id=f"{request.run2_id}_{idx}", run_id=request.run2_id,
                    distance=float(row["distance"]), clock_position=float(row["clock_position"]),
                    depth_pct=float(row["depth_pct"]), length=float(row["length"]),
                    width=float(row["width"]), feature_type=row["feature_type"],
                    inspection_date=date2,
                ))
            except Exception:
                pass

        # Match and analyze growth
        matcher = HungarianMatcher(confidence_threshold=0.6)
        result = matcher.match_anomalies(anomalies_1, anomalies_2, request.run1_id, request.run2_id)

        analyzer = GrowthAnalyzer()
        growth_result = analyzer.analyze_matches(
            result["matches"], anomalies_1, anomalies_2, time_interval
        )

        stats = growth_result["statistics"]
        metrics = [
            GrowthMetricsResponse(
                match_id=gm.match_id,
                depth_growth_rate=gm.depth_growth_rate,
                length_growth_rate=gm.length_growth_rate,
                width_growth_rate=gm.width_growth_rate,
                is_rapid_growth=gm.is_rapid_growth,
                risk_score=gm.risk_score,
            )
            for gm in growth_result["growth_metrics"]
        ]

        return GrowthCalculationResponse(
            total_matches=stats["total_matches"],
            rapid_growth_count=stats["rapid_growth_count"],
            rapid_growth_percentage=stats["rapid_growth_percentage"],
            avg_depth_growth=stats["depth_growth"].get("mean", 0.0),
            max_depth_growth=stats["depth_growth"].get("max", 0.0),
            metrics=metrics,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Data file not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Growth calculation failed: {str(e)}")


@router.get("/growth/trajectories", response_model=TrajectoriesResponse)
async def get_growth_trajectories(req: Request):
    """
    Get growth trajectories for all chains (for visualization).

    Requires a completed three-way analysis in the store.
    """
    store = req.app.state.analysis_store

    # Find the most recent completed analysis
    latest_result = None
    for aid, entry in store.items():
        if entry["status"] == "COMPLETE" and entry.get("result"):
            latest_result = entry["result"]

    if not latest_result:
        raise HTTPException(
            status_code=404,
            detail="No completed analysis found. Run POST /api/analyze/three-way first.",
        )

    trajectories = []
    for chain in latest_result.chains:
        projected_year = None
        if chain.years_to_80pct is not None and chain.years_to_80pct > 0:
            projected_year = 2022 + int(chain.years_to_80pct)

        traj = GrowthTrajectoryResponse(
            chain_id=chain.chain_id,
            points=[
                TrajectoryPoint(year=2007, depth_pct=chain.depth_2007, growth_rate=None),
                TrajectoryPoint(year=2015, depth_pct=chain.depth_2015, growth_rate=chain.growth_rate_07_15),
                TrajectoryPoint(year=2022, depth_pct=chain.depth_2022, growth_rate=chain.growth_rate_15_22),
            ],
            acceleration=chain.acceleration,
            is_accelerating=chain.is_accelerating,
            projected_80pct_year=projected_year,
        )
        trajectories.append(traj)

    return TrajectoriesResponse(
        trajectories=trajectories,
        total=len(trajectories),
    )

