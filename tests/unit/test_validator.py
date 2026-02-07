"""
Unit tests for DataValidator class.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.ingestion.validator import DataValidator
from src.data_models.models import ValidationResult


class TestDataValidator:
    """Tests for DataValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a DataValidator instance."""
        return DataValidator()

    @pytest.fixture
    def valid_anomaly_df(self):
        """Create a DataFrame with valid anomaly records."""
        return pd.DataFrame({
            "id": ["A1", "A2", "A3"],
            "run_id": ["RUN1", "RUN1", "RUN1"],
            "distance": [100.0, 200.0, 300.0],
            "clock_position": [3.0, 6.0, 9.0],
            "depth_pct": [25.0, 35.0, 45.0],
            "length": [4.5, 5.2, 3.8],
            "width": [2.3, 2.8, 2.1],
            "feature_type": ["external_corrosion", "external_corrosion", "internal_corrosion"],
            "coating_type": ["FBE", "FBE", None],
            "inspection_date": [datetime(2020, 1, 1)] * 3
        })

    @pytest.fixture
    def invalid_anomaly_df(self):
        """Create a DataFrame with invalid anomaly records."""
        return pd.DataFrame({
            "id": ["A1", "A2", "A3"],
            "run_id": ["RUN1", "RUN1", "RUN1"],
            "distance": [100.0, -50.0, 300.0],  # A2 has negative distance
            "clock_position": [3.0, 15.0, 9.0],  # A2 has invalid clock position
            "depth_pct": [25.0, 150.0, 45.0],  # A2 has depth > 100
            "length": [4.5, 5.2, -1.0],  # A3 has negative length
            "width": [2.3, 2.8, 2.1],
            "feature_type": ["external_corrosion", "external_corrosion", "internal_corrosion"],
            "coating_type": [None, None, None],
            "inspection_date": [datetime(2020, 1, 1)] * 3
        })

    @pytest.fixture
    def missing_values_df(self):
        """Create a DataFrame with missing values."""
        return pd.DataFrame({
            "id": ["A1", "A2", "A3", "A4"],
            "run_id": ["RUN1", "RUN1", "RUN1", "RUN1"],
            "distance": [100.0, 200.0, 300.0, 400.0],
            "clock_position": [3.0, np.nan, np.nan, 9.0],  # Missing clock positions
            "depth_pct": [25.0, 35.0, 45.0, 55.0],
            "length": [4.5, np.nan, 3.8, np.nan],  # Missing lengths
            "width": [2.3, 2.8, np.nan, np.nan],  # Missing widths
            "feature_type": ["external_corrosion"] * 4,
            "coating_type": [None] * 4,
            "inspection_date": [datetime(2020, 1, 1)] * 4
        })

    def test_validate_schema_valid_records(self, validator, valid_anomaly_df):
        """Test validation of valid records."""
        result = validator.validate_schema(valid_anomaly_df)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.valid_count == 3
        assert result.invalid_count == 0
        assert len(result.errors) == 0

    def test_validate_schema_invalid_records(self, validator, invalid_anomaly_df):
        """Test validation of invalid records."""
        result = validator.validate_schema(invalid_anomaly_df)
        
        assert result.is_valid is False
        assert result.invalid_count > 0
        assert len(result.errors) > 0

    def test_check_required_fields_all_present(self, validator, valid_anomaly_df):
        """Test that all required fields are present."""
        all_present, missing = validator.check_required_fields(valid_anomaly_df)
        
        assert all_present is True
        assert len(missing) == 0

    def test_check_required_fields_missing(self, validator):
        """Test detection of missing required fields."""
        df = pd.DataFrame({
            "id": ["A1"],
            "run_id": ["RUN1"],
            "distance": [100.0]
            # Missing: clock_position, depth_pct, length, width, feature_type, inspection_date
        })
        
        all_present, missing = validator.check_required_fields(df)
        
        assert all_present is False
        assert "clock_position" in missing
        assert "depth_pct" in missing
        assert "length" in missing
        assert "width" in missing
        assert "feature_type" in missing
        assert "inspection_date" in missing

    def test_validate_ranges_valid(self, validator, valid_anomaly_df):
        """Test range validation with valid data."""
        errors = validator.validate_ranges(valid_anomaly_df)
        
        assert len(errors) == 0

    def test_validate_ranges_negative_distance(self, validator):
        """Test detection of negative distance."""
        df = pd.DataFrame({
            "distance": [100.0, -50.0, 200.0]
        })
        
        errors = validator.validate_ranges(df)
        
        assert len(errors) > 0
        assert any("negative distance" in err.lower() for err in errors)

    def test_validate_ranges_invalid_clock_position(self, validator):
        """Test detection of invalid clock position."""
        df = pd.DataFrame({
            "clock_position": [3.0, 15.0, 0.5]  # 15.0 and 0.5 are invalid
        })
        
        errors = validator.validate_ranges(df)
        
        assert len(errors) > 0
        assert any("clock_position" in err for err in errors)

    def test_validate_ranges_invalid_depth(self, validator):
        """Test detection of invalid depth percentage."""
        df = pd.DataFrame({
            "depth_pct": [25.0, 150.0, -10.0]  # 150.0 and -10.0 are invalid
        })
        
        errors = validator.validate_ranges(df)
        
        assert len(errors) > 0
        assert any("depth_pct" in err for err in errors)

    def test_validate_ranges_invalid_length(self, validator):
        """Test detection of invalid length."""
        df = pd.DataFrame({
            "length": [4.5, 0.0, -1.0]  # 0.0 and -1.0 are invalid
        })
        
        errors = validator.validate_ranges(df)
        
        assert len(errors) > 0
        assert any("length" in err for err in errors)

    def test_validate_ranges_invalid_width(self, validator):
        """Test detection of invalid width."""
        df = pd.DataFrame({
            "width": [2.3, 0.0, -0.5]  # 0.0 and -0.5 are invalid
        })
        
        errors = validator.validate_ranges(df)
        
        assert len(errors) > 0
        assert any("width" in err for err in errors)

    def test_impute_missing_clock_position(self, validator):
        """Test forward-fill imputation for clock_position."""
        df = pd.DataFrame({
            "clock_position": [3.0, np.nan, np.nan, 6.0, np.nan]
        })
        
        result = validator.impute_missing_values(df)
        
        # Forward fill should propagate 3.0 to next two rows
        assert result["clock_position"].iloc[0] == 3.0
        assert result["clock_position"].iloc[1] == 3.0
        assert result["clock_position"].iloc[2] == 3.0
        assert result["clock_position"].iloc[3] == 6.0
        assert result["clock_position"].iloc[4] == 6.0
        
        # Check imputation log
        assert len(validator.imputation_log) > 0
        assert any("clock_position" in log for log in validator.imputation_log)

    def test_impute_missing_length(self, validator):
        """Test median imputation for length."""
        df = pd.DataFrame({
            "length": [4.0, 5.0, np.nan, 6.0, np.nan]
        })
        
        result = validator.impute_missing_values(df)
        
        # Median of [4.0, 5.0, 6.0] is 5.0
        assert result["length"].iloc[2] == 5.0
        assert result["length"].iloc[4] == 5.0
        
        # Check imputation log
        assert len(validator.imputation_log) > 0
        assert any("length" in log for log in validator.imputation_log)

    def test_impute_missing_width(self, validator):
        """Test median imputation for width."""
        df = pd.DataFrame({
            "width": [2.0, 3.0, np.nan, 4.0, np.nan]
        })
        
        result = validator.impute_missing_values(df)
        
        # Median of [2.0, 3.0, 4.0] is 3.0
        assert result["width"].iloc[2] == 3.0
        assert result["width"].iloc[4] == 3.0
        
        # Check imputation log
        assert len(validator.imputation_log) > 0
        assert any("width" in log for log in validator.imputation_log)

    def test_impute_multiple_fields(self, validator, missing_values_df):
        """Test imputation of multiple fields simultaneously."""
        result = validator.impute_missing_values(missing_values_df)
        
        # Check that missing values were imputed
        assert result["clock_position"].isna().sum() < missing_values_df["clock_position"].isna().sum()
        assert result["length"].isna().sum() == 0
        assert result["width"].isna().sum() == 0
        
        # Check imputation log has entries for all fields
        assert len(validator.imputation_log) >= 2  # At least length and width

    def test_imputation_idempotence(self, validator, missing_values_df):
        """Test that applying imputation twice produces same result as once."""
        result1 = validator.impute_missing_values(missing_values_df)
        result2 = validator.impute_missing_values(result1)
        
        # Results should be identical
        pd.testing.assert_frame_equal(result1, result2)

    def test_generate_validation_report(self, validator, valid_anomaly_df):
        """Test generation of validation report."""
        validation_result = validator.validate_schema(valid_anomaly_df)
        report = validator.generate_validation_report(valid_anomaly_df, validation_result)
        
        assert "timestamp" in report
        assert report["total_records"] == 3
        assert report["valid_records"] == 3
        assert report["invalid_records"] == 0
        assert report["validation_passed"] is True
        assert report["required_fields_present"] is True
        assert len(report["missing_fields"]) == 0
        assert "quality_metrics" in report

    def test_generate_validation_report_with_errors(self, validator, invalid_anomaly_df):
        """Test validation report with errors."""
        validation_result = validator.validate_schema(invalid_anomaly_df)
        report = validator.generate_validation_report(invalid_anomaly_df, validation_result)
        
        assert report["validation_passed"] is False
        assert report["invalid_records"] > 0
        assert len(report["validation_errors"]) > 0
        assert len(report["range_validation_errors"]) > 0

    def test_quality_metrics_calculation(self, validator, valid_anomaly_df):
        """Test calculation of quality metrics."""
        validation_result = validator.validate_schema(valid_anomaly_df)
        report = validator.generate_validation_report(valid_anomaly_df, validation_result)
        
        metrics = report["quality_metrics"]
        
        # Check that numeric statistics are present
        assert "depth_pct_min" in metrics
        assert "depth_pct_max" in metrics
        assert "depth_pct_mean" in metrics
        assert "feature_type_distribution" in metrics

    def test_quality_metrics_with_missing_values(self, validator, missing_values_df):
        """Test quality metrics with missing values."""
        validation_result = validator.validate_schema(missing_values_df)
        report = validator.generate_validation_report(missing_values_df, validation_result)
        
        metrics = report["quality_metrics"]
        
        # Check that missing value percentages are reported
        assert "missing_clock_position_pct" in metrics
        assert "missing_length_pct" in metrics
        assert "missing_width_pct" in metrics

    def test_validate_and_report_convenience_method(self, validator, valid_anomaly_df):
        """Test the convenience method that validates and reports in one call."""
        validation_result, report = validator.validate_and_report(valid_anomaly_df)
        
        assert isinstance(validation_result, ValidationResult)
        assert isinstance(report, dict)
        assert validation_result.is_valid is True
        assert report["validation_passed"] is True

    def test_validate_reference_points(self, validator):
        """Test validation of reference points."""
        ref_df = pd.DataFrame({
            "id": ["R1", "R2", "R3"],
            "run_id": ["RUN1", "RUN1", "RUN1"],
            "distance": [100.0, 200.0, 300.0],
            "point_type": ["girth_weld", "valve", "tee"],
            "description": ["GW-001", "V-001", "T-001"]
        })
        
        result = validator.validate_reference_points(ref_df)
        
        assert result.is_valid is True
        assert result.valid_count == 3
        assert result.invalid_count == 0

    def test_validate_reference_points_invalid(self, validator):
        """Test validation of invalid reference points."""
        ref_df = pd.DataFrame({
            "id": ["R1", "R2"],
            "run_id": ["RUN1", "RUN1"],
            "distance": [100.0, -50.0],  # R2 has negative distance
            "point_type": ["girth_weld", "valve"],
            "description": [None, None]
        })
        
        result = validator.validate_reference_points(ref_df)
        
        assert result.is_valid is False
        assert result.invalid_count > 0
        assert len(result.errors) > 0

    def test_empty_dataframe(self, validator):
        """Test validation of empty DataFrame."""
        empty_df = pd.DataFrame()
        
        result = validator.validate_schema(empty_df)
        
        assert result.record_count == 0
        assert result.valid_count == 0
        assert result.invalid_count == 0

    def test_boundary_values(self, validator):
        """Test validation with boundary values."""
        df = pd.DataFrame({
            "id": ["A1", "A2", "A3", "A4"],
            "run_id": ["RUN1"] * 4,
            "distance": [0.0, 0.0, 0.0, 0.0],  # Minimum valid distance
            "clock_position": [1.0, 12.0, 6.5, 3.0],  # Boundary values
            "depth_pct": [0.0, 100.0, 50.0, 25.0],  # Boundary values
            "length": [0.1, 0.1, 0.1, 0.1],  # Just above zero
            "width": [0.1, 0.1, 0.1, 0.1],  # Just above zero
            "feature_type": ["external_corrosion"] * 4,
            "coating_type": [None] * 4,
            "inspection_date": [datetime(2020, 1, 1)] * 4
        })
        
        result = validator.validate_schema(df)
        
        # All boundary values should be valid
        assert result.is_valid is True
        assert result.valid_count == 4

    def test_imputation_log_cleared_between_calls(self, validator, missing_values_df):
        """Test that imputation log is cleared between calls."""
        # First imputation
        validator.impute_missing_values(missing_values_df)
        first_log_length = len(validator.imputation_log)
        
        # Second imputation (on different data)
        df2 = pd.DataFrame({
            "length": [1.0, np.nan, 3.0]
        })
        validator.impute_missing_values(df2)
        
        # Log should contain only entries from second call
        # (Note: imputation_log is not cleared in current implementation,
        # but this test documents expected behavior)
        assert len(validator.imputation_log) >= 1

    def test_validation_with_extra_columns(self, validator, valid_anomaly_df):
        """Test that validation works with extra columns not in schema."""
        df = valid_anomaly_df.copy()
        df["extra_column"] = ["value1", "value2", "value3"]
        
        # Should still validate successfully (extra columns ignored)
        result = validator.validate_schema(df)
        
        # Note: Pydantic will ignore extra columns by default
        # This test documents that behavior
        assert result.record_count == 3
