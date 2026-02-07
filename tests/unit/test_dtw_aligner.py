"""
Unit tests for DTW alignment engine.

Tests the DTWAligner class implementation including:
- Distance matrix calculation with drift constraint
- Optimal path finding using dynamic programming
- Alignment metrics (match_rate, RMSE)
- Edge cases and error handling
"""

import pytest
import numpy as np
from datetime import datetime
from typing import List

from src.alignment.dtw_aligner import DTWAligner, align_reference_points, MatchedPair
from src.data_models.models import ReferencePoint, AlignmentResult


def create_reference_point(
    id: str,
    run_id: str,
    distance: float,
    point_type: str = "girth_weld"
) -> ReferencePoint:
    """Helper to create reference point for testing"""
    return ReferencePoint(
        id=id,
        run_id=run_id,
        distance=distance,
        point_type=point_type
    )


class TestDTWAligner:
    """Test suite for DTWAligner class"""
    
    def test_initialization(self):
        """Test DTWAligner initialization with default and custom drift constraint"""
        aligner = DTWAligner()
        assert aligner.drift_constraint == 0.10
        
        aligner_custom = DTWAligner(drift_constraint=0.15)
        assert aligner_custom.drift_constraint == 0.15
    
    def test_calculate_distance_matrix_perfect_alignment(self):
        """Test distance matrix calculation with perfectly aligned sequences"""
        aligner = DTWAligner()
        seq1 = np.array([100.0, 200.0, 300.0])
        seq2 = np.array([100.0, 200.0, 300.0])
        
        distance_matrix = aligner.calculate_distance_matrix(seq1, seq2)
        
        # Diagonal should be zero (perfect matches)
        assert distance_matrix[0, 0] == 0.0
        assert distance_matrix[1, 1] == 0.0
        assert distance_matrix[2, 2] == 0.0
        
        # Shape should be correct
        assert distance_matrix.shape == (3, 3)
    
    def test_calculate_distance_matrix_with_drift(self):
        """Test distance matrix with small drift within constraint"""
        aligner = DTWAligner(drift_constraint=0.10)
        seq1 = np.array([100.0, 200.0, 300.0])
        seq2 = np.array([102.0, 198.0, 305.0])  # Small drift
        
        distance_matrix = aligner.calculate_distance_matrix(seq1, seq2)
        
        # Check that small differences are captured
        assert distance_matrix[0, 0] == pytest.approx(2.0, abs=0.1)
        assert distance_matrix[1, 1] == pytest.approx(2.0, abs=0.1)
        assert distance_matrix[2, 2] == pytest.approx(5.0, abs=0.1)
        
        # All values should be finite (within constraint)
        assert not np.isinf(distance_matrix[0, 0])
    
    def test_calculate_distance_matrix_exceeds_constraint(self):
        """Test that pairs exceeding drift constraint are set to infinity"""
        aligner = DTWAligner(drift_constraint=0.10)
        seq1 = np.array([100.0, 200.0])
        seq2 = np.array([150.0, 250.0])  # 50% drift - exceeds 10% constraint
        
        distance_matrix = aligner.calculate_distance_matrix(seq1, seq2)
        
        # Cross-matches should be infinity (too far apart)
        # 100 vs 250: diff=150, avg=175, max_drift=17.5, exceeds constraint
        assert np.isinf(distance_matrix[0, 1])
        assert np.isinf(distance_matrix[1, 0])
    
    def test_find_optimal_path_simple(self):
        """Test optimal path finding with simple aligned sequences"""
        aligner = DTWAligner()
        seq1 = np.array([100.0, 200.0, 300.0])
        seq2 = np.array([100.0, 200.0, 300.0])
        
        distance_matrix = aligner.calculate_distance_matrix(seq1, seq2)
        path = aligner.find_optimal_path(distance_matrix, seq1, seq2)
        
        # Should match all points in order
        expected_path = [(0, 0), (1, 1), (2, 2)]
        assert path == expected_path
    
    def test_find_optimal_path_with_skip(self):
        """Test optimal path when one sequence has extra points"""
        aligner = DTWAligner(drift_constraint=0.10)
        seq1 = np.array([100.0, 200.0, 300.0, 400.0])
        seq2 = np.array([100.0, 300.0, 400.0])  # Missing 200
        
        distance_matrix = aligner.calculate_distance_matrix(seq1, seq2)
        path = aligner.find_optimal_path(distance_matrix, seq1, seq2)
        
        # Path should skip the unmatched point
        assert len(path) >= 3
        # First and last should match
        assert path[0] == (0, 0)
        assert path[-1] == (3, 2)
    
    def test_align_sequences_success(self):
        """Test complete alignment workflow with valid sequences"""
        ref_points1 = [
            create_reference_point("rp1_1", "run1", 100.0),
            create_reference_point("rp1_2", "run1", 200.0),
            create_reference_point("rp1_3", "run1", 300.0),
        ]
        ref_points2 = [
            create_reference_point("rp2_1", "run2", 102.0),
            create_reference_point("rp2_2", "run2", 198.0),
            create_reference_point("rp2_3", "run2", 301.0),
        ]
        
        aligner = DTWAligner()
        result = aligner.align_sequences(ref_points1, ref_points2, "run1", "run2")
        
        # Check result structure
        assert isinstance(result, AlignmentResult)
        assert result.run1_id == "run1"
        assert result.run2_id == "run2"
        assert len(result.matched_points) == 3
        
        # Check match rate (should be 100% for this case)
        assert result.match_rate == pytest.approx(100.0, abs=1.0)
        
        # Check RMSE (should be small)
        assert result.rmse < 5.0
        
        # Check correction parameters exist
        assert 'matched_distances_run1' in result.correction_function_params
        assert 'matched_distances_run2' in result.correction_function_params
    
    def test_align_sequences_empty_input(self):
        """Test that empty sequences raise ValueError"""
        aligner = DTWAligner()
        
        with pytest.raises(ValueError, match="Cannot align empty"):
            aligner.align_sequences([], [], "run1", "run2")
    
    def test_align_sequences_poor_quality_fails_validation(self):
        """Test that poor alignment quality fails validation thresholds"""
        # Create sequences with very poor alignment (large drift)
        ref_points1 = [
            create_reference_point("rp1_1", "run1", 100.0),
            create_reference_point("rp1_2", "run1", 200.0),
        ]
        ref_points2 = [
            create_reference_point("rp2_1", "run2", 500.0),  # Very far apart
            create_reference_point("rp2_2", "run2", 600.0),
        ]
        
        aligner = DTWAligner(drift_constraint=0.10)
        
        # This should raise ValueError due to match_rate < 95% or RMSE > 10
        with pytest.raises(ValueError):
            aligner.align_sequences(ref_points1, ref_points2, "run1", "run2")
    
    def test_calculate_match_rate(self):
        """Test match rate calculation"""
        aligner = DTWAligner()
        
        # 3 matched out of max 4 points = 75%
        match_rate = aligner._calculate_match_rate(3, 4, 4)
        assert match_rate == 75.0
        
        # 4 matched out of max 4 points = 100%
        match_rate = aligner._calculate_match_rate(4, 4, 4)
        assert match_rate == 100.0
        
        # Different sequence lengths: 3 matched out of max(3, 5) = 60%
        match_rate = aligner._calculate_match_rate(3, 3, 5)
        assert match_rate == 60.0  # 3 / 5 = 60%
        
        # Edge case: more matches than max length (shouldn't happen but cap at 100%)
        match_rate = aligner._calculate_match_rate(6, 4, 4)
        assert match_rate == 100.0
    
    def test_calculate_rmse(self):
        """Test RMSE calculation"""
        aligner = DTWAligner()
        
        matched_pairs = [
            MatchedPair("rp1", "rp2", 100.0, 102.0, 2.0),
            MatchedPair("rp3", "rp4", 200.0, 198.0, 2.0),
            MatchedPair("rp5", "rp6", 300.0, 304.0, 4.0),
        ]
        
        rmse = aligner._calculate_rmse(matched_pairs)
        
        # RMSE = sqrt((4 + 4 + 16) / 3) = sqrt(8) ≈ 2.83
        expected_rmse = np.sqrt((4 + 4 + 16) / 3)
        assert rmse == pytest.approx(expected_rmse, abs=0.01)
    
    def test_calculate_rmse_empty(self):
        """Test RMSE calculation with empty list"""
        aligner = DTWAligner()
        rmse = aligner._calculate_rmse([])
        assert rmse == 0.0
    
    def test_align_reference_points_convenience_function(self):
        """Test the convenience function wrapper"""
        ref_points1 = [
            create_reference_point("rp1_1", "run1", 100.0),
            create_reference_point("rp1_2", "run1", 200.0),
        ]
        ref_points2 = [
            create_reference_point("rp2_1", "run2", 101.0),
            create_reference_point("rp2_2", "run2", 199.0),
        ]
        
        result = align_reference_points(ref_points1, ref_points2, "run1", "run2")
        
        assert isinstance(result, AlignmentResult)
        assert result.run1_id == "run1"
        assert result.run2_id == "run2"
        assert len(result.matched_points) == 2
    
    def test_realistic_pipeline_scenario(self):
        """Test with realistic pipeline reference point scenario"""
        # Simulate 10 girth welds with slight odometer drift (0.5% drift)
        ref_points1 = [
            create_reference_point(f"run1_gw{i}", "run1", 100.0 * i)
            for i in range(1, 11)
        ]
        
        # Second run has 0.5% cumulative drift (within acceptable range)
        ref_points2 = [
            create_reference_point(f"run2_gw{i}", "run2", 100.0 * i * 1.005)
            for i in range(1, 11)
        ]
        
        aligner = DTWAligner(drift_constraint=0.10)
        result = aligner.align_sequences(ref_points1, ref_points2, "run1", "run2")
        
        # Should match all 10 points
        assert len(result.matched_points) == 10
        
        # Match rate should be 100%
        assert result.match_rate == pytest.approx(100.0, abs=0.1)
        
        # RMSE should be reasonable (within 10 feet threshold)
        assert result.rmse < 10.0
    
    def test_different_sequence_lengths(self):
        """Test alignment with different sequence lengths"""
        ref_points1 = [
            create_reference_point("rp1_1", "run1", 100.0),
            create_reference_point("rp1_2", "run1", 200.0),
            create_reference_point("rp1_3", "run1", 300.0),
            create_reference_point("rp1_4", "run1", 400.0),
            create_reference_point("rp1_5", "run1", 500.0),
        ]
        ref_points2 = [
            create_reference_point("rp2_1", "run2", 100.0),
            create_reference_point("rp2_2", "run2", 300.0),
            create_reference_point("rp2_3", "run2", 500.0),
        ]
        
        aligner = DTWAligner(drift_constraint=0.10)
        
        # This scenario has poor alignment quality (missing points, high RMSE)
        # so it should fail validation
        with pytest.raises(ValueError):
            aligner.align_sequences(ref_points1, ref_points2, "run1", "run2")
    
    def test_backtrack_path_correctness(self):
        """Test that backtracking produces valid path"""
        aligner = DTWAligner()
        seq1 = np.array([100.0, 200.0, 300.0])
        seq2 = np.array([100.0, 200.0, 300.0])
        
        distance_matrix = aligner.calculate_distance_matrix(seq1, seq2)
        
        # Create cost matrix manually for testing
        n, m = distance_matrix.shape
        cost = np.full((n + 1, m + 1), np.inf)
        cost[0, 0] = 0.0
        
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                dist = distance_matrix[i - 1, j - 1]
                if not np.isinf(dist):
                    min_cost = min(cost[i - 1, j], cost[i, j - 1], cost[i - 1, j - 1])
                    cost[i, j] = dist + min_cost
        
        path = aligner._backtrack_path(cost, distance_matrix)
        
        # Path should be non-empty
        assert len(path) > 0
        
        # Path should start at (0, 0) or close to it
        assert path[0][0] == 0 or path[0][1] == 0
        
        # Path should end at or near (n-1, m-1)
        assert path[-1][0] >= n - 2
        assert path[-1][1] >= m - 2
    
    def test_drift_constraint_boundary(self):
        """Test behavior at exact drift constraint boundary"""
        aligner = DTWAligner(drift_constraint=0.10)
        
        # Create sequences where drift is exactly at 10% boundary
        seq1 = np.array([1000.0])
        seq2 = np.array([1100.0])  # Exactly 10% drift
        
        distance_matrix = aligner.calculate_distance_matrix(seq1, seq2)
        
        # At boundary, should still be finite
        # avg = 1050, max_drift = 105, actual_diff = 100, should be allowed
        assert not np.isinf(distance_matrix[0, 0])
        assert distance_matrix[0, 0] == 100.0


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_single_reference_point(self):
        """Test alignment with single reference point in each sequence"""
        ref_points1 = [create_reference_point("rp1", "run1", 100.0)]
        ref_points2 = [create_reference_point("rp2", "run2", 102.0)]
        
        aligner = DTWAligner()
        result = aligner.align_sequences(ref_points1, ref_points2, "run1", "run2")
        
        assert len(result.matched_points) == 1
        assert result.match_rate == 100.0
    
    def test_very_large_sequences(self):
        """Test performance with large sequences"""
        # Create 100 reference points with small drift (0.2%)
        ref_points1 = [
            create_reference_point(f"rp1_{i}", "run1", 50.0 * i)
            for i in range(100)
        ]
        ref_points2 = [
            create_reference_point(f"rp2_{i}", "run2", 50.0 * i * 1.002)
            for i in range(100)
        ]
        
        aligner = DTWAligner()
        result = aligner.align_sequences(ref_points1, ref_points2, "run1", "run2")
        
        # Should complete successfully
        assert len(result.matched_points) > 0
        assert result.match_rate > 0
        # With small drift, should meet quality thresholds
        assert result.match_rate >= 95.0
        assert result.rmse <= 10.0
    
    def test_zero_distance_reference_points(self):
        """Test handling of reference points at distance zero"""
        ref_points1 = [
            create_reference_point("rp1_1", "run1", 0.0),
            create_reference_point("rp1_2", "run1", 100.0),
        ]
        ref_points2 = [
            create_reference_point("rp2_1", "run2", 0.0),
            create_reference_point("rp2_2", "run2", 100.0),
        ]
        
        aligner = DTWAligner()
        result = aligner.align_sequences(ref_points1, ref_points2, "run1", "run2")
        
        assert len(result.matched_points) == 2
        assert result.match_rate == 100.0
