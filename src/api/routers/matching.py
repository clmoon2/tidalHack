"""
Matching Router
===============

Endpoints for anomaly matching between two runs.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException

from src.api.schemas.requests import MatchAnomaliesRequest
from src.api.schemas.responses import MatchingResultResponse, MatchResponse

router = APIRouter()


@router.post("/match/anomalies", response_model=MatchingResultResponse)
async def match_anomalies(request: MatchAnomaliesRequest):
    """
    Match anomalies between two inspection runs using the Hungarian algorithm.

    Takes paths to two CSV files and returns matched anomaly pairs
    with similarity scores and confidence levels.
    """
    try:
        from src.ingestion.loader import ILIDataLoader
        from src.data_models.models import AnomalyRecord
        from src.matching.matcher import HungarianMatcher
        from src.matching.similarity import SimilarityCalculator

        loader = ILIDataLoader()

        # Parse dates
        date1 = datetime.fromisoformat(request.run1_date) if request.run1_date else datetime(2020, 1, 1)
        date2 = datetime.fromisoformat(request.run2_date) if request.run2_date else datetime(2022, 1, 1)

        # Load datasets
        df1, _ = loader.load_and_process(request.run1_path, request.run1_id, date1)
        df2, _ = loader.load_and_process(request.run2_path, request.run2_id, date2)

        anomalies_1 = []
        for idx, row in df1.iterrows():
            try:
                anomalies_1.append(AnomalyRecord(
                    id=f"{request.run1_id}_{idx}",
                    run_id=request.run1_id,
                    distance=float(row["distance"]),
                    clock_position=float(row["clock_position"]),
                    depth_pct=float(row["depth_pct"]),
                    length=float(row["length"]),
                    width=float(row["width"]),
                    feature_type=row["feature_type"],
                    inspection_date=date1,
                ))
            except Exception:
                pass

        anomalies_2 = []
        for idx, row in df2.iterrows():
            try:
                anomalies_2.append(AnomalyRecord(
                    id=f"{request.run2_id}_{idx}",
                    run_id=request.run2_id,
                    distance=float(row["distance"]),
                    clock_position=float(row["clock_position"]),
                    depth_pct=float(row["depth_pct"]),
                    length=float(row["length"]),
                    width=float(row["width"]),
                    feature_type=row["feature_type"],
                    inspection_date=date2,
                ))
            except Exception:
                pass

        # Run matching
        sim_calc = SimilarityCalculator(
            distance_sigma=request.distance_sigma,
            clock_sigma=request.clock_sigma,
        )
        matcher = HungarianMatcher(
            similarity_calculator=sim_calc,
            confidence_threshold=request.confidence_threshold,
        )
        result = matcher.match_anomalies(
            anomalies_1, anomalies_2, request.run1_id, request.run2_id
        )

        stats = result["statistics"]
        matches = [
            MatchResponse(
                match_id=m.id,
                anomaly1_id=m.anomaly1_id,
                anomaly2_id=m.anomaly2_id,
                similarity_score=m.similarity_score,
                confidence=m.confidence,
                distance_similarity=m.distance_similarity,
                clock_similarity=m.clock_similarity,
                type_similarity=m.type_similarity,
                depth_similarity=m.depth_similarity,
            )
            for m in result["matches"]
        ]

        return MatchingResultResponse(
            run1_id=request.run1_id,
            run2_id=request.run2_id,
            total_run1=stats["total_run1"],
            total_run2=stats["total_run2"],
            matched=stats["matched"],
            match_rate=stats["match_rate"],
            high_confidence=stats["high_confidence"],
            medium_confidence=stats["medium_confidence"],
            low_confidence=stats["low_confidence"],
            matches=matches,
            new_anomalies=stats["unmatched_run2"],
            repaired_anomalies=stats["unmatched_run1"],
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Data file not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")

