"""
Anomalies Router
================

Endpoints for retrieving anomalies by run.
"""

from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException

from src.api.schemas.responses import AnomaliesListResponse, AnomalyResponse

router = APIRouter()

# Mapping from run IDs to file paths
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


@router.get("/anomalies/{run_id}", response_model=AnomaliesListResponse)
async def get_anomalies_by_run(run_id: str):
    """
    Get all anomalies for a specific inspection run.

    Supported run_ids: RUN_2007, RUN_2015, RUN_2022, RUN_2020
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

        loader = ILIDataLoader()
        date = RUN_DATE_MAP.get(run_id, datetime(2022, 1, 1))
        df, _ = loader.load_and_process(file_path, run_id, date)

        anomalies = []
        for idx, row in df.iterrows():
            try:
                anomalies.append(
                    AnomalyResponse(
                        id=f"{run_id}_{idx}",
                        run_id=run_id,
                        distance=float(row["distance"]),
                        clock_position=float(row["clock_position"]),
                        depth_pct=float(row["depth_pct"]),
                        length=float(row["length"]),
                        width=float(row["width"]),
                        feature_type=row["feature_type"],
                    )
                )
            except Exception:
                pass

        return AnomaliesListResponse(
            run_id=run_id,
            anomalies=anomalies,
            total=len(anomalies),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load anomalies: {str(e)}")

