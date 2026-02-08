"""
Clusters Router
===============

Endpoint for retrieving ASME B31G interaction zones (anomaly clusters)
for a given inspection run.
"""

from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException

from src.api.schemas.responses import (
    ClustersListResponse,
    InteractionZoneResponse,
)

router = APIRouter()

# Mapping from run IDs to file paths (mirrors anomalies router)
RUN_FILE_MAP = {
    "RUN_2007": "data/ILIDataV2_2007.csv",
    "RUN_2015": "data/ILIDataV2_2015.csv",
    "RUN_2022": "data/ILIDataV2_2022.csv",
    "RUN_2020": "data/sample_run_2020.csv",
}

RUN_DATE_MAP = {
    "RUN_2007": datetime(2007, 1, 1),
    "RUN_2015": datetime(2015, 1, 1),
    "RUN_2022": datetime(2022, 1, 1),
    "RUN_2020": datetime(2020, 1, 1),
}


@router.get("/clusters/{run_id}", response_model=ClustersListResponse)
async def get_clusters_by_run(
    run_id: str,
    axial_threshold_ft: float = 1.0,
    clock_threshold: float = 1.5,
    min_cluster_size: int = 2,
):
    """
    Detect and return ASME B31G interaction zones for a given run.

    Runs DBSCAN clustering on the anomalies of the specified inspection run
    using the provided proximity thresholds.

    Query params:
        axial_threshold_ft: Max axial separation in feet (default 1.0)
        clock_threshold: Max circumferential separation in clock hours (default 1.5)
        min_cluster_size: Minimum anomalies to form a cluster (default 2)
    """
    if run_id not in RUN_FILE_MAP:
        raise HTTPException(
            status_code=404,
            detail=f"Run '{run_id}' not found. Available: {list(RUN_FILE_MAP.keys())}",
        )

    file_path = RUN_FILE_MAP[run_id]
    if not Path(file_path).exists():
        raise HTTPException(
            status_code=404,
            detail=f"Data file not found: {file_path}",
        )

    try:
        from src.ingestion.loader import ILIDataLoader
        from src.data_models.models import AnomalyRecord
        from src.analysis.cluster_detector import ClusterDetector

        # Load anomalies
        loader = ILIDataLoader()
        date = RUN_DATE_MAP.get(run_id, datetime(2022, 1, 1))
        df, _ = loader.load_and_process(file_path, run_id, date)

        anomalies = []
        for idx, row in df.iterrows():
            try:
                anomalies.append(
                    AnomalyRecord(
                        id=f"{run_id}_{idx}",
                        run_id=run_id,
                        distance=float(row["distance"]),
                        clock_position=float(row["clock_position"]),
                        depth_pct=float(row["depth_pct"]),
                        length=float(row["length"]),
                        width=float(row["width"]),
                        feature_type=row["feature_type"],
                        inspection_date=date,
                    )
                )
            except Exception:
                pass

        # Run clustering
        detector = ClusterDetector(
            axial_threshold_ft=axial_threshold_ft,
            clock_threshold=clock_threshold,
            min_cluster_size=min_cluster_size,
        )
        updated_anomalies, zones = detector.detect_clusters(anomalies, run_id)

        clustered_count = sum(1 for a in updated_anomalies if a.cluster_id is not None)
        clustered_pct = (clustered_count / len(updated_anomalies) * 100) if updated_anomalies else 0.0

        zone_responses = [
            InteractionZoneResponse(
                zone_id=z.zone_id,
                run_id=z.run_id,
                anomaly_ids=z.anomaly_ids,
                anomaly_count=z.anomaly_count,
                centroid_distance=z.centroid_distance,
                centroid_clock=z.centroid_clock,
                span_distance_ft=z.span_distance_ft,
                span_clock=z.span_clock,
                max_depth_pct=z.max_depth_pct,
                combined_length_in=z.combined_length_in,
            )
            for z in zones
        ]

        return ClustersListResponse(
            run_id=run_id,
            zones=zone_responses,
            total_zones=len(zones),
            clustered_anomaly_count=clustered_count,
            total_anomaly_count=len(updated_anomalies),
            clustered_pct=round(clustered_pct, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect clusters: {str(e)}",
        )

