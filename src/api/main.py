"""
FastAPI Application
===================

Main FastAPI application for the ILI Data Alignment System.

Provides REST API endpoints and webhook receivers for frontend integration.
"""

import os
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import analysis, matching, growth, anomalies, explain, reports, webhooks, chains


# ─── In-memory store for analysis results ─────────────────────────────
# In production, this would be a database
analysis_store: dict = {}
anomaly_store: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    print("=" * 60)
    print("  ILI Data Alignment System - API Server Starting")
    print("=" * 60)
    # Check for available datasets
    data_dir = Path("data")
    datasets = []
    for f in ["ILIDataV2_2007.csv", "ILIDataV2_2015.csv", "ILIDataV2_2022.csv"]:
        if (data_dir / f).exists():
            datasets.append(f)
    app.state.available_datasets = datasets
    app.state.analysis_store = analysis_store
    app.state.anomaly_store = anomaly_store
    print(f"  Datasets available: {len(datasets)}")
    print(f"  AI agents: {'enabled' if os.getenv('GOOGLE_API_KEY') else 'disabled'}")
    print("=" * 60)
    yield
    print("  API Server shutting down...")


app = FastAPI(
    title="ILI Data Alignment System API",
    description=(
        "REST API for pipeline In-Line Inspection (ILI) data alignment, "
        "anomaly matching, growth analysis, and AI-powered explanations. "
        "Supports three-way analysis (2007→2015→2022) with multi-agent storytelling."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS middleware ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for hackathon demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Include routers ─────────────────────────────────────────────────
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(matching.router, prefix="/api", tags=["Matching"])
app.include_router(growth.router, prefix="/api", tags=["Growth"])
app.include_router(anomalies.router, prefix="/api", tags=["Anomalies"])
app.include_router(explain.router, prefix="/api", tags=["AI Explain"])
app.include_router(reports.router, prefix="/api", tags=["Reports"])
app.include_router(chains.router, prefix="/api", tags=["Chains"])
app.include_router(webhooks.router, prefix="/webhook", tags=["Webhooks"])


# ─── Health check ────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat(),
        "agents_available": bool(os.getenv("GOOGLE_API_KEY")),
        "datasets_available": getattr(app.state, "available_datasets", []),
    }


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "ILI Data Alignment System API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "analysis": "/api/analyze/three-way",
            "chains": "/api/chains",
            "matching": "/api/match/anomalies",
            "growth": "/api/growth/calculate",
            "anomalies": "/api/anomalies/{run_id}",
            "explain": "/api/explain/chain",
            "reports": "/api/reports/summary",
            "webhooks": "/webhook/analyze",
        },
    }

