"""
Unit tests for DistanceCorrectionFunction.

Tests piecewise linear interpolation, extrapolation handling,
and integration with DTW alignment results.

Requirements: 2.6
"""

import pytest
import numpy as np
import pandas as pd
from src.alignment.correction import (
    DistanceCorrectionFunction,
    create_correction_function
)
from src.data_models.models import AlignmentResult


class TestDistanceCorrectionFunctionInit:
    """Test initialization and validation of DistanceCorrectionFunction."""
    
    def test_valid_initialization(self):
        """Test successful initialization with valid parameters."""
        params = {
            'matched_distances_run1': [100.0, 200.0, 300.0],
            'matched_distances_run2': [102.0, 205.0, 297.0],
            'interpolation_method': 'linear'
        }
        
        corrector = DistanceCorrectionFunction(params)
        
        assert corrector.method == 'linear'
        assert len(corrector.distances_run1) == 3
        assert len(corrector.distances_run2) == 3
        assert corrector.min_distance_run1 == 100.0
        assert corrector.max_distance_run1 == 300.0
    
    def test_empty_distances_raises_error(self):
        """Test that empty distance arrays raise ValueError."""
        params = {
            'matched_distances_run1': [],
            'matched_distances_run2': [],
            'interpolation_method': 'linear'
        }
        
        with pytest.raises(ValueError, match="empty distance arrays"):
            DistanceCorrectionFunction(params)
    
    def test_mismatched_lengths_raises_error(self):
        """Test that mismatched array lengths raise ValueError."""
        params = {
            'matched_distances_run1': [100.0, 200.0, 300.0],
            'matched_distances_run2': [102.0, 205.0],  # Only 2 elements
            'interpolation_method': 'linear'
        }
        
        with pytest.raises(ValueError, match="same length"):
            DistanceCorrectionFunction(params)
    
    def test_insufficient_points_raises_error(self):
        """Test that less than 2 points raises ValueError."""
        params = {
            'matched_distances_run1': [100.0],
            'matched_distances_run2': [102.0],
            'interpolation_method': 'linear'
        }
        
        with pytest.raises(ValueError, match="at least 2 matched points"):
            DistanceCorrectionFunction(params)
    
    def test_default_interpolation_method(self):
        """Test that default interpolation method is 'linear'."""
        params = {
            'matched_distances_run1': [100.0, 200.0],
            'matched_distances_run2': [102.0, 205.0]
            # No interpolation_method specified
        }
        
        corrector = DistanceCorrectionFunction(params)
        assert corrector.method == 'linear'


class TestDistanceCorrectionInterpolation:
    """Test interpolation within reference point range."""
    
    @pytest.fixture
    def simple_corrector(self):
        """Create a simple correction function for testing."""
        params = {
            'matched_distances_run1': [0.0, 100.0, 200.0],
            'matched_distances_run2': [0.0, 110.0, 200.0],
            'interpolation_method': 'linear'
        }
        return DistanceCorrectionFunction(params)
    
    def test_exact_match_points(self, simple_corrector):
        """Test that matched reference points return exact values."""
        assert simple_corrector.correct_distance(0.0) == pytest.approx(0.0)
        assert simple_corrector.correct_distance(100.0) == pytest.approx(110.0)
        assert simple_corrector.correct_distance(200.0) == pytest.approx(200.0)
    
    def test_interpolation_between_points(self, simple_corrector):
        """Test linear interpolation between reference points."""
        # Between 0 and 100: slope = (110-0)/(100-0) = 1.1
        assert simple_corrector.correct_distance(50.0) == pytest.approx(55.0)
        
        # Between 100 and 200: slope = (200-110)/(200-100) = 0.9
        assert simple_corrector.correct_distance(150.0) == pytest.approx(155.0)
    
    def test_multiple_distances_at_once(self, simple_corrector):
        """Test correcting multiple distances in one call."""
        distances = [0.0, 50.0, 100.0, 150.0, 200.0]
        corrected = simple_corrector.correct_distance(distances)
        
        expected = [0.0, 55.0, 110.0, 155.0, 200.0]
        np.testing.assert_array_almost_equal(corrected, expected)
    
    def test_numpy_array_input(self, simple_corrector):
        """Test that numpy array input works correctly."""
        distances = np.array([50.0, 100.0, 150.0])
        corrected = simple_corrector.correct_distance(distances)
        
        assert isinstance(corrected, np.ndarray)
        assert len(corrected) == 3
    
    def test_list_input(self, simple_corrector):
        """Test that list input works correctly."""
        distances = [50.0, 100.0, 150.0]
        corrected = simple_corrector.correct_distance(distances)
        
        assert isinstance(corrected, np.ndarray)
        assert len(corrected) == 3


class TestDistanceCorrectionExtrapolation:
    """Test extrapolation beyond reference point range."""
    
    @pytest.fixture
    def corrector(self):
        """Create correction function for extrapolation testing."""
        params = {
            'matched_distances_run1': [100.0, 200.0, 300.0],
            'matched_distances_run2': [102.0, 205.0, 297.0],
            'interpolation_method': 'linear'
        }
        return DistanceCorrectionFunction(params)
    
    def test_extrapolation_below_range(self, corrector):
        """Test extrapolation for distances below minimum reference point."""
        # Below 100.0 - should extrapolate linearly
        corrected = corrector.correct_distance(50.0)
        
        # Should follow the trend from first two points
        assert isinstance(corrected, float)
        assert corrected < 102.0  # Should be less than first corrected point
    
    def test_extrapolation_above_range(self, corrector):
        """Test extrapolation for distances above maximum reference point."""
        # Above 300.0 - should extrapolate linearly
        corrected = corrector.correct_distance(350.0)
        
        # Should follow the trend from last two points
        assert isinstance(corrected, float)
        assert corrected > 297.0  # Should be greater than last corrected point
    
    def test_is_extrapolating_method(self, corrector):
        """Test is_extrapolating method correctly identifies extrapolation."""
        # Within range
        assert not corrector.is_extrapolating(150.0)
        assert not corrector.is_extrapolating(100.0)
        assert not corrector.is_extrapolating(300.0)
        
        # Outside range
        assert corrector.is_extrapolating(50.0)
        assert corrector.is_extrapolating(350.0)


class TestDistanceCorrectionDataFrame:
    """Test DataFrame operations for anomaly correction."""
    
    @pytest.fixture
    def corrector(self):
        """Create correction function for DataFrame testing."""
        params = {
            'matched_distances_run1': [0.0, 1000.0, 2000.0],
            'matched_distances_run2': [0.0, 1020.0, 1980.0],
            'interpolation_method': 'linear'
        }
        return DistanceCorrectionFunction(params)
    
    @pytest.fixture
    def anomalies_df(self):
        """Create sample anomalies DataFrame."""
        return pd.DataFrame({
            'id': ['A1', 'A2', 'A3', 'A4'],
            'distance': [100.0, 500.0, 1000.0, 1500.0],
            'depth_pct': [25.0, 30.0, 35.0, 40.0],
            'feature_type': ['external_corrosion'] * 4
        })
    
    def test_correct_anomaly_distances(self, corrector, anomalies_df):
        """Test correcting all anomaly distances in DataFrame."""
        result_df = corrector.correct_anomaly_distances(anomalies_df)
        
        # Check that corrected_distance column was added
        assert 'corrected_distance' in result_df.columns
        
        # Check that original distance column is preserved
        assert 'distance' in result_df.columns
        pd.testing.assert_series_equal(
            result_df['distance'],
            anomalies_df['distance']
        )
        
        # Check that corrections were applied
        assert len(result_df) == len(anomalies_df)
        assert all(result_df['corrected_distance'].notna())
    
    def test_custom_column_names(self, corrector, anomalies_df):
        """Test using custom column names for correction."""
        result_df = corrector.correct_anomaly_distances(
            anomalies_df,
            distance_column='distance',
            corrected_column='distance_run2'
        )
        
        assert 'distance_run2' in result_df.columns
        assert 'corrected_distance' not in result_df.columns
    
    def test_missing_distance_column_raises_error(self, corrector, anomalies_df):
        """Test that missing distance column raises ValueError."""
        with pytest.raises(ValueError, match="not found in DataFrame"):
            corrector.correct_anomaly_distances(
                anomalies_df,
                distance_column='nonexistent_column'
            )
    
    def test_original_dataframe_not_modified(self, corrector, anomalies_df):
        """Test that original DataFrame is not modified."""
        original_columns = set(anomalies_df.columns)
        
        result_df = corrector.correct_anomaly_distances(anomalies_df)
        
        # Original should be unchanged
        assert set(anomalies_df.columns) == original_columns
        assert 'corrected_distance' not in anomalies_df.columns


class TestDistanceCorrectionInfo:
    """Test correction function information methods."""
    
    @pytest.fixture
    def corrector(self):
        """Create correction function with known properties."""
        params = {
            'matched_distances_run1': [100.0, 200.0, 300.0, 400.0],
            'matched_distances_run2': [105.0, 210.0, 295.0, 405.0],
            'interpolation_method': 'linear'
        }
        return DistanceCorrectionFunction(params)
    
    def test_get_correction_info(self, corrector):
        """Test that correction info returns expected structure."""
        info = corrector.get_correction_info()
        
        # Check all expected keys are present
        assert 'num_reference_points' in info
        assert 'distance_range_run1' in info
        assert 'distance_range_run2' in info
        assert 'interpolation_method' in info
        assert 'max_correction' in info
        assert 'mean_correction' in info
        assert 'std_correction' in info
        
        # Check values
        assert info['num_reference_points'] == 4
        assert info['distance_range_run1'] == (100.0, 400.0)
        assert info['distance_range_run2'] == (105.0, 405.0)
        assert info['interpolation_method'] == 'linear'
    
    def test_correction_statistics(self, corrector):
        """Test that correction statistics are calculated correctly."""
        info = corrector.get_correction_info()
        
        # Corrections: [5.0, 10.0, -5.0, 5.0]
        # Max absolute: 10.0
        # Mean: 3.75
        assert info['max_correction'] == pytest.approx(10.0)
        assert info['mean_correction'] == pytest.approx(3.75)
        assert info['std_correction'] > 0  # Should have some variation


class TestDistanceCorrectionRealWorld:
    """Test with realistic ILI data scenarios."""
    
    def test_typical_odometer_drift(self):
        """Test correction with typical 5% odometer drift."""
        # Simulate 5% cumulative drift over 10,000 feet
        distances_run1 = np.linspace(0, 10000, 20)
        # Run2 has 5% drift (500 feet over 10,000 feet)
        distances_run2 = distances_run1 * 1.05
        
        params = {
            'matched_distances_run1': distances_run1.tolist(),
            'matched_distances_run2': distances_run2.tolist(),
            'interpolation_method': 'linear'
        }
        
        corrector = DistanceCorrectionFunction(params)
        
        # Test correction at midpoint
        corrected = corrector.correct_distance(5000.0)
        assert corrected == pytest.approx(5250.0, rel=0.01)
    
    def test_non_uniform_drift(self):
        """Test correction with non-uniform drift pattern."""
        # Simulate drift that varies along pipeline
        params = {
            'matched_distances_run1': [0.0, 1000.0, 2000.0, 3000.0],
            'matched_distances_run2': [0.0, 1050.0, 1980.0, 3030.0],
            'interpolation_method': 'linear'
        }
        
        corrector = DistanceCorrectionFunction(params)
        
        # Test that interpolation handles varying drift
        corrected_500 = corrector.correct_distance(500.0)
        corrected_1500 = corrector.correct_distance(1500.0)
        corrected_2500 = corrector.correct_distance(2500.0)
        
        # All should be valid numbers
        assert all(isinstance(c, float) for c in [corrected_500, corrected_1500, corrected_2500])
        assert all(c > 0 for c in [corrected_500, corrected_1500, corrected_2500])
    
    def test_minimal_drift(self):
        """Test correction with minimal drift (high quality alignment)."""
        # Very small drift - less than 1 foot per 1000 feet
        params = {
            'matched_distances_run1': [0.0, 1000.0, 2000.0, 3000.0],
            'matched_distances_run2': [0.0, 1000.5, 2001.0, 3000.2],
            'interpolation_method': 'linear'
        }
        
        corrector = DistanceCorrectionFunction(params)
        
        # Corrections should be very small
        info = corrector.get_correction_info()
        assert info['max_correction'] < 2.0  # Less than 2 feet max correction


class TestCreateCorrectionFunction:
    """Test convenience function for creating correction from AlignmentResult."""
    
    def test_create_from_alignment_result(self):
        """Test creating correction function from AlignmentResult."""
        # Create mock AlignmentResult
        alignment = AlignmentResult(
            run1_id='run1',
            run2_id='run2',
            matched_points=[('rp1', 'rp2'), ('rp3', 'rp4')],
            match_rate=95.0,
            rmse=8.5,
            correction_function_params={
                'matched_distances_run1': [100.0, 200.0, 300.0],
                'matched_distances_run2': [102.0, 205.0, 297.0],
                'interpolation_method': 'linear'
            }
        )
        
        corrector = create_correction_function(alignment)
        
        assert isinstance(corrector, DistanceCorrectionFunction)
        assert corrector.method == 'linear'
        assert len(corrector.distances_run1) == 3
    
    def test_integration_with_dtw_output(self):
        """Test that correction function works with actual DTW output format."""
        # This simulates the exact structure from DTWAligner
        alignment = AlignmentResult(
            run1_id='run1',
            run2_id='run2',
            matched_points=[('rp1', 'rp2'), ('rp3', 'rp4'), ('rp5', 'rp6')],
            match_rate=100.0,
            rmse=5.2,
            correction_function_params={
                'matched_distances_run1': [0.0, 500.0, 1000.0],
                'matched_distances_run2': [0.0, 510.0, 995.0],
                'interpolation_method': 'linear'
            }
        )
        
        corrector = create_correction_function(alignment)
        
        # Test that it can correct distances
        corrected = corrector.correct_distance(250.0)
        assert isinstance(corrected, float)
        assert 0.0 < corrected < 1000.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_single_segment_pipeline(self):
        """Test with minimum number of reference points (2)."""
        params = {
            'matched_distances_run1': [0.0, 1000.0],
            'matched_distances_run2': [0.0, 1050.0],
            'interpolation_method': 'linear'
        }
        
        corrector = DistanceCorrectionFunction(params)
        
        # Should work with just 2 points
        assert corrector.correct_distance(500.0) == pytest.approx(525.0)
    
    def test_zero_distance(self):
        """Test correction at distance zero."""
        params = {
            'matched_distances_run1': [0.0, 100.0, 200.0],
            'matched_distances_run2': [0.0, 105.0, 195.0],
            'interpolation_method': 'linear'
        }
        
        corrector = DistanceCorrectionFunction(params)
        
        # Zero should map to zero
        assert corrector.correct_distance(0.0) == 0.0
    
    def test_negative_correction(self):
        """Test that negative corrections (shrinkage) work correctly."""
        # Run2 is shorter than Run1
        params = {
            'matched_distances_run1': [0.0, 1000.0, 2000.0],
            'matched_distances_run2': [0.0, 950.0, 1900.0],
            'interpolation_method': 'linear'
        }
        
        corrector = DistanceCorrectionFunction(params)
        
        # Corrections should be negative
        info = corrector.get_correction_info()
        assert info['mean_correction'] < 0
        
        # Test actual correction
        corrected = corrector.correct_distance(1000.0)
        assert corrected == 950.0
    
    def test_unsorted_reference_points(self):
        """Test that unsorted reference points are handled correctly."""
        # Provide points in non-sorted order
        params = {
            'matched_distances_run1': [200.0, 100.0, 300.0],  # Not sorted
            'matched_distances_run2': [205.0, 102.0, 297.0],
            'interpolation_method': 'linear'
        }
        
        # Should not raise error - scipy handles sorting
        corrector = DistanceCorrectionFunction(params)
        
        # Should still work correctly
        corrected = corrector.correct_distance(150.0)
        assert isinstance(corrected, float)
