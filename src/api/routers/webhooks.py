"""
Webhooks Router
===============

Webhook receivers for frontend integration.
Frontend triggers analysis via webhooks, then polls REST endpoints for results.
"""

import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile, File, Form

from src.api.schemas.requests import WebhookAnalyzeRequest
from src.api.schemas.responses import WebhookResponse, UploadResponse

router = APIRouter()


@router.post("/analyze", response_model=WebhookResponse)
async def webhook_analyze(
    request: WebhookAnalyzeRequest,
    background_tasks: BackgroundTasks,
    req: Request,
):
    """
    Receive "analyze" trigger from frontend.

    Starts a three-way analysis in the background. Returns an analysis_id
    that can be polled via GET /api/analysis/{analysis_id}.

    Flow:
    1. Frontend POSTs to this webhook with data paths
    2. Backend starts analysis (may take 30-60s)
    3. Frontend polls GET /api/analysis/{id} for status
    4. When complete, frontend fetches data via REST endpoints
    """
    analysis_id = str(uuid.uuid4())[:8]
    store = req.app.state.analysis_store

    # Default paths if not provided
    data_2007 = request.data_2007_path or "data/ILIDataV2_2007.csv"
    data_2015 = request.data_2015_path or "data/ILIDataV2_2015.csv"
    data_2022 = request.data_2022_path or "data/ILIDataV2_2022.csv"

    store[analysis_id] = {
        "status": "PENDING",
        "progress_pct": 0.0,
        "message": "Analysis triggered via webhook",
        "created_at": datetime.now(),
        "completed_at": None,
        "result": None,
    }

    # Import here to avoid circular imports
    from src.api.schemas.requests import ThreeWayAnalysisRequest
    from src.api.routers.analysis import _run_analysis_background

    analysis_request = ThreeWayAnalysisRequest(
        data_2007_path=data_2007,
        data_2015_path=data_2015,
        data_2022_path=data_2022,
        top_n_explain=request.top_n_explain,
        use_agents=request.use_agents,
    )

    background_tasks.add_task(
        _run_analysis_background, analysis_id, analysis_request, store
    )

    return WebhookResponse(
        success=True,
        message="Analysis started successfully",
        analysis_id=analysis_id,
        status_url=f"/api/analysis/{analysis_id}",
    )


@router.post("/upload", response_model=UploadResponse)
async def webhook_upload(
    file: UploadFile = File(...),
    run_id: str = Form(...),
    inspection_date: Optional[str] = Form(None),
):
    """
    Receive uploaded CSV data from frontend.

    Saves the file and loads it into the system for analysis.
    """
    # Validate file type
    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Only CSV and Excel files are supported",
        )

    # Save uploaded file
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / f"{run_id}_{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Try to load and validate
    try:
        from src.ingestion.loader import ILIDataLoader

        loader = ILIDataLoader()
        date = (
            datetime.fromisoformat(inspection_date)
            if inspection_date
            else datetime.now()
        )
        anomalies_df, ref_df = loader.load_and_process(str(file_path), run_id, date)

        return UploadResponse(
            success=True,
            message=f"File uploaded and validated: {file.filename}",
            run_id=run_id,
            anomaly_count=len(anomalies_df),
            reference_point_count=len(ref_df),
        )

    except Exception as e:
        # Clean up file on failure
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"File validation failed: {str(e)}",
        )

