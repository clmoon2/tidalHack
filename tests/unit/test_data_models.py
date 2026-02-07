"""
Unit tests for Pydantic data models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from src.data_models import (
    AnomalyRecord,
    ReferencePoint,
    Match,
    GrowthMetrics,
    Prediction,
    AlignmentResult,
)


class TestAnomalyRecord:
    """Tests for AnomalyRecord model."""

    def test_valid_anomaly_record(self):
        """Test creating a valid anomaly record."""
        record = AnomalyRecord(
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
        )
        assert record.id == "A1"
        assert record.clock_position == 3.0
        assert record.depth_pct == 25.0

    def test_invalid_clock_position_below_range(self):
        """Test that clock position below 1 raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            AnomalyRecord(
                id="A1",
                run_id="RUN1",
                distance=100.0,
                clock_position=0.5,  # Invalid: below 1
                depth_pct=25.0,
                length=4.5,
                width=2.3,
                feature_type="external_corrosion",
                inspection_date=datetime(2020, 1, 1),
            )
        assert "clock_position" in str(exc_info.value)

    def test_invalid_clock_position_above_range(self):
        """Test that clock position above 12 raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            AnomalyRecord(
                id="A1",
                run_id="RUN1",
                distance=100.0,
                clock_position=13.0,  # Invalid: above 12
                depth_pct=25.0,
                length=4.5,
                width=2.3,
                feature_type="external_corrosion",
                inspection_date=datetime(2020, 1, 1),
            )
        assert "clock_position" in str(exc_info.value)

    def test_invalid_negative_distance(self):
        """Test that negative distance raises validation error."""
        with pytest.raises(ValidationError):
            AnomalyRecord(
                id="A1",
                run_id="RUN1",
                distance=-10.0,  # Invalid: negative
                clock_position=3.0,
                depth_pct=25.0,
                length=4.5,
                width=2.3,
                feature_type="external_corrosion",
                inspection_date=datetime(2020, 1, 1),
            )

    def test_invalid_depth_above_100(self):
        """Test that depth above 100% raises validation error."""
        with pytest.raises(ValidationError):
            AnomalyRecord(
                id="A1",
                run_id="RUN1",
                distance=100.0,
                clock_position=3.0,
                depth_pct=150.0,  # Invalid: above 100
                length=4.5,
                width=2.3,
                feature_type="external_corrosion",
                inspection_date=datetime(2020, 1, 1),
            )


class TestMatch:
    """Tests for Match model."""

    def test_confidence_high(self):
        """Test that similarity >= 0.8 sets confidence to HIGH."""
        match = Match(
            id="M1",
            anomaly1_id="A1",
            anomaly2_id="A2",
            similarity_score=0.85,
            distance_similarity=0.9,
            clock_similarity=0.8,
            type_similarity=1.0,
            depth_similarity=0.85,
            length_similarity=0.8,
            width_similarity=0.75,
        )
        assert match.confidence == "HIGH"

    def test_confidence_medium(self):
        """Test that 0.6 <= similarity < 0.8 sets confidence to MEDIUM."""
        match = Match(
            id="M1",
            anomaly1_id="A1",
            anomaly2_id="A2",
            similarity_score=0.7,
            distance_similarity=0.75,
            clock_similarity=0.7,
            type_similarity=1.0,
            depth_similarity=0.65,
            length_similarity=0.6,
            width_similarity=0.6,
        )
        assert match.confidence == "MEDIUM"

    def test_confidence_low(self):
        """Test that similarity < 0.6 sets confidence to LOW."""
        match = Match(
            id="M1",
            anomaly1_id="A1",
            anomaly2_id="A2",
            similarity_score=0.5,
            distance_similarity=0.6,
            clock_similarity=0.5,
            type_similarity=0.0,
            depth_similarity=0.5,
            length_similarity=0.5,
            width_similarity=0.5,
        )
        assert match.confidence == "LOW"


class TestGrowthMetrics:
    """Tests for GrowthMetrics model."""

    def test_rapid_growth_detection(self):
        """Test that growth rate > 5% sets is_rapid_growth to True."""
        metrics = GrowthMetrics(
            match_id="M1",
            time_interval_years=5.0,
            depth_growth_rate=6.0,  # > 5.0 threshold
            length_growth_rate=0.5,
            width_growth_rate=0.3,
            risk_score=0.75,
        )
        assert metrics.is_rapid_growth is True

    def test_normal_growth_detection(self):
        """Test that growth rate <= 5% sets is_rapid_growth to False."""
        metrics = GrowthMetrics(
            match_id="M1",
            time_interval_years=5.0,
            depth_growth_rate=3.0,  # <= 5.0 threshold
            length_growth_rate=0.5,
            width_growth_rate=0.3,
            risk_score=0.45,
        )
        assert metrics.is_rapid_growth is False


class TestAlignmentResult:
    """Tests for AlignmentResult model."""

    def test_valid_alignment_result(self):
        """Test creating a valid alignment result."""
        result = AlignmentResult(
            run1_id="RUN1",
            run2_id="RUN2",
            matched_points=[("R1", "R2"), ("R3", "R4")],
            match_rate=96.5,
            rmse=8.2,
            correction_function_params={"method": "linear"},
        )
        assert result.match_rate == 96.5
        assert result.rmse == 8.2

    def test_invalid_match_rate_below_threshold(self):
        """Test that match rate < 95% raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            AlignmentResult(
                run1_id="RUN1",
                run2_id="RUN2",
                matched_points=[("R1", "R2")],
                match_rate=90.0,  # Below 95% threshold
                rmse=8.2,
                correction_function_params={"method": "linear"},
            )
        assert "Match rate below 95% threshold" in str(exc_info.value)

    def test_invalid_rmse_above_threshold(self):
        """Test that RMSE > 10 feet raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            AlignmentResult(
                run1_id="RUN1",
                run2_id="RUN2",
                matched_points=[("R1", "R2")],
                match_rate=96.5,
                rmse=12.5,  # Above 10 feet threshold
                correction_function_params={"method": "linear"},
            )
        assert "RMSE exceeds 10 feet threshold" in str(exc_info.value)


class TestReferencePoint:
    """Tests for ReferencePoint model."""

    def test_valid_reference_point(self):
        """Test creating a valid reference point."""
        ref_point = ReferencePoint(
            id="R1",
            run_id="RUN1",
            distance=100.0,
            point_type="girth_weld",
            description="GW-001",
        )
        assert ref_point.id == "R1"
        assert ref_point.point_type == "girth_weld"

    def test_invalid_negative_distance(self):
        """Test that negative distance raises validation error."""
        with pytest.raises(ValidationError):
            ReferencePoint(
                id="R1",
                run_id="RUN1",
                distance=-50.0,  # Invalid: negative
                point_type="girth_weld",
            )
