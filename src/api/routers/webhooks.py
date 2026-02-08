"""
Webhooks Router
===============

Webhook receivers for frontend integration.
Frontend triggers analysis via webhooks, then polls REST endpoints for results.
"""

import uuid
import math
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse

from src.api.schemas.requests import WebhookAnalyzeRequest
from src.api.schemas.responses import WebhookResponse, UploadResponse, WebAppAnomaly

router = APIRouter()


# ─── Helper: risk scoring (mirrors webapp riskCalculation.ts) ────────

def _normalise(value: float, lo: float, hi: float) -> float:
    if hi == lo:
        return 0.0
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def _compute_risk_score(
    depth_pct: float,
    length: float,
    operating_pressure: float,
    growth_rate: float = 0.0,
    erf: float = 0.0,
) -> int:
    """
    Return 0-100 risk score.

    When ERF (Estimated Repair Factor) is available from the ILI data it is
    used as a major component because it already encodes depth, length,
    operating pressure, and wall thickness via the B31G calculation.

    Normalisation ranges are calibrated against real pipeline data:
      - depth_pct 0-80 %  (80 % = critical threshold per 49 CFR §192.933)
      - length    0-50 in (typical anomaly range in ILI reports)
      - pressure  100-1500 PSI
      - ERF       0.3-1.1 (1.0 = at safe-pressure limit)
      - growth    0-10 pp/yr
    """
    if erf > 0:
        # ERF-informed scoring (2015/2022 data)
        score = (
            0.30 * _normalise(depth_pct, 0, 80)
            + 0.10 * _normalise(length, 0, 50)
            + 0.10 * _normalise(operating_pressure, 100, 1500)
            + 0.40 * _normalise(erf, 0.3, 1.1)
            + 0.10 * _normalise(growth_rate, 0, 10)
        )
    else:
        # Geometry-only scoring (2007 data or when ERF unavailable)
        score = (
            0.45 * _normalise(depth_pct, 0, 80)
            + 0.25 * _normalise(length, 0, 50)
            + 0.20 * _normalise(operating_pressure, 100, 1500)
            + 0.10 * _normalise(growth_rate, 0, 10)
        )
    return round(score * 100)


def _risk_level(score: int) -> str:
    if score >= 80:
        return "Critical"
    if score >= 60:
        return "High"
    if score >= 40:
        return "Moderate"
    return "Low"


def _compliance(depth_pct: float, length: float):
    """Return (action_required, regulatory_basis) matching webapp logic."""
    if depth_pct >= 80:
        return "Immediate repair required", "49 CFR §192.933(d)(1)"
    if depth_pct >= 50 and length >= 25:
        return "Repair within 180 days", "49 CFR §192.933(d)(2)"
    return "Continue monitoring", "49 CFR §192.933"


# ─── Analyze webhook (unchanged) ────────────────────────────────────

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


# ─── Upload webhook (returns full anomaly list for webapp) ──────────

@router.post("/upload")
async def webhook_upload(
    file: UploadFile = File(...),
    runId: str = Form(...),
    inspection_date: Optional[str] = Form(None),
    nominalWallThickness: Optional[float] = Form(None),
    pipelineDiameter: Optional[float] = Form(None),
    operatingPressure: Optional[float] = Form(None),
    materialGrade: Optional[str] = Form(None),
):
    """
    Receive uploaded CSV/XLSX data from the webapp.

    Loads the file, computes risk scores for every anomaly, and returns
    the full anomaly list in the camelCase format expected by the
    webapp ``BackendService``.
    """
    # Validate file type
    if not file.filename or not file.filename.endswith((".csv", ".xlsx", ".xls")):
        return JSONResponse(
            status_code=400,
            content={"success": False, "anomalies": [], "error": "Only CSV and Excel files are supported"},
        )

    # Pipeline metadata defaults
    wall_thickness = nominalWallThickness if nominalWallThickness is not None else 10.0
    diameter = pipelineDiameter if pipelineDiameter is not None else 24.0
    pressure = operatingPressure if operatingPressure is not None else 720.0
    grade = materialGrade or "X52"

    # Numeric run_id (the webapp sends "1", "2", "3")
    try:
        numeric_run_id = int(runId)
    except ValueError:
        numeric_run_id = 1

    # Save uploaded file
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / f"{runId}_{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        from src.ingestion.loader import ILIDataLoader

        loader = ILIDataLoader()
        date = (
            datetime.fromisoformat(inspection_date)
            if inspection_date
            else datetime.now()
        )
        anomalies_df, _ref_df = loader.load_and_process(str(file_path), runId, date)

        # ── Extract pipeline-level MOP from the CSV if available ──
        # The column mapping normalises various header names to "mop_psi".
        if "mop_psi" in anomalies_df.columns:
            mop_series = pd.to_numeric(anomalies_df["mop_psi"], errors="coerce")
            median_mop = mop_series.median()
            if not math.isnan(median_mop) and median_mop > 0:
                pressure = float(median_mop)

        # ── Extract wall thickness from the CSV if available ──
        if "wall_thickness" in anomalies_df.columns:
            wt_series = pd.to_numeric(anomalies_df["wall_thickness"], errors="coerce")
            median_wt = wt_series.median()
            if not math.isnan(median_wt) and median_wt > 0:
                wall_thickness = float(median_wt)

        # Build webapp-compatible anomaly objects
        anomalies: list[WebAppAnomaly] = []
        for _idx, row in anomalies_df.iterrows():
            depth = float(row.get("depth_pct", 0) or 0)
            length_val = float(row.get("length", 0) or 0)
            width_val = float(row.get("width", 0) or 0)
            dist = float(row.get("distance", 0) or 0)

            # Clamp clock position to 1-12 (required by webapp validation)
            raw_clock = row.get("clock_position", 6)
            if raw_clock is None or (isinstance(raw_clock, float) and math.isnan(raw_clock)):
                clock = 6.0  # default to 6 o'clock
            else:
                clock = max(1.0, min(12.0, float(raw_clock)))

            # Clamp depth to 0-100
            depth = max(0.0, min(100.0, depth))

            # ── Per-row MOP (fall back to file-level median) ──
            row_pressure = pressure
            raw_mop = row.get("mop_psi")
            if raw_mop is not None:
                try:
                    p = float(raw_mop)
                    if not math.isnan(p) and p > 0:
                        row_pressure = p
                except (ValueError, TypeError):
                    pass

            # ── Per-row ERF (Estimated Repair Factor) ──
            row_erf = 0.0
            raw_erf = row.get("erf")
            if raw_erf is not None:
                try:
                    e = float(raw_erf)
                    if not math.isnan(e) and e > 0:
                        row_erf = e
                except (ValueError, TypeError):
                    pass

            # Compute risk (now uses real MOP + ERF when available)
            risk_score = _compute_risk_score(
                depth, length_val, row_pressure,
                growth_rate=0.0, erf=row_erf,
            )
            risk_score = max(0, min(100, risk_score))
            level = _risk_level(risk_score)
            action, basis = _compliance(depth, length_val)

            feature_id = str(row.get("id", f"WL-{runId}{_idx}"))
            insp_date = date.isoformat() if date else datetime.now().isoformat()

            anomalies.append(
                WebAppAnomaly(
                    feature_id=feature_id,
                    distance=dist,
                    clock_position=round(clock, 2),
                    depth_percent=round(depth, 2),
                    length=round(length_val, 2),
                    width=round(width_val, 2),
                    risk_score=risk_score,
                    risk_level=level,
                    action_required=action,
                    regulatory_basis=basis,
                    run_id=numeric_run_id,
                    inspection_date=insp_date,
                    nominal_wall_thickness=wall_thickness,
                    pipeline_diameter=diameter,
                    operating_pressure=row_pressure,
                    material_grade=grade,
                    growth_rate=None,
                )
            )

        response = UploadResponse(
            success=True,
            anomalies=anomalies,
            message=f"Loaded {len(anomalies)} anomalies from {file.filename}",
        )

        # Serialize with camelCase aliases
        return JSONResponse(
            content=response.model_dump(by_alias=True),
        )

    except Exception as e:
        # Clean up file on failure
        file_path.unlink(missing_ok=True)
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "anomalies": [],
                "error": f"File processing failed: {str(e)}",
            },
        )

