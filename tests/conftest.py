"""
Pytest configuration and shared fixtures.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List
from src.data_models.models import AnomalyRecord, ReferencePoint


@pytest.fixture
def sample_anomaly_data() -> pd.DataFrame:
    """Generate sample anomaly data for testing."""
    return pd.DataFrame(
        {
            "id": ["A1", "A2", "A3"],
            "run_id": ["RUN1", "RUN1", "RUN1"],
            "distance": [100.0, 200.0, 300.0],
            "clock_position": [3.0, 6.0, 9.0],
            "depth_pct": [25.0, 35.0, 45.0],
            "length": [4.5, 5.2, 6.1],
            "width": [2.3, 3.1, 3.8],
            "feature_type": ["external_corrosion", "internal_corrosion", "external_corrosion"],
            "coating_type": ["FBE", "FBE", "3LPE"],
            "inspection_date": [datetime(2020, 1, 1)] * 3,
        }
    )


@pytest.fixture
def sample_reference_points() -> pd.DataFrame:
    """Generate sample reference points for testing."""
    return pd.DataFrame(
        {
            "id": ["R1", "R2", "R3"],
            "run_id": ["RUN1", "RUN1", "RUN1"],
            "distance": [50.0, 150.0, 250.0],
            "point_type": ["girth_weld", "valve", "girth_weld"],
            "description": ["GW-001", "VALVE-A", "GW-002"],
        }
    )


@pytest.fixture
def sample_anomaly_records() -> List[AnomalyRecord]:
    """Generate sample AnomalyRecord objects for testing."""
    return [
        AnomalyRecord(
            id="A1",
            run_id="RUN1",
            distance=100.0,
            clock_position=3.0,
            depth_pct=25.0,
            length=4.5,
            width=2.3,
            feature_type="external_corrosion",
            coating_type="FBE",
            inspection_date=datetime(2020, 1, 1),
        ),
        AnomalyRecord(
            id="A2",
            run_id="RUN1",
            distance=200.0,
            clock_position=6.0,
            depth_pct=35.0,
            length=5.2,
            width=3.1,
            feature_type="internal_corrosion",
            coating_type="FBE",
            inspection_date=datetime(2020, 1, 1),
        ),
    ]


@pytest.fixture
def temp_database(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_ili.db"
    return str(db_path)
