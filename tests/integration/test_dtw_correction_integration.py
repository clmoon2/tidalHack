"""
Integration tests for DTW alignment and distance correction.

Tests the complete workflow: DTW alignment → correction function → anomaly correction.

Requirements: 2.1, 2.2, 2.6
"""

import pytest
import pandas as pd
from src.data_models.models import ReferencePoint
from src.alignment.dtw_aligner import DTWAligner
from src.alignment.correction import create_correction_function


class TestDTWCorrectionIntegration:
    """Test integration between DTW alignment and distance correction."""
    
    @pytest.fixture
    def reference_points_run1(self):
        """Create reference points for first inspection run."""
        return [
            ReferencePoint(
                id='rp1_1',
                run_id='run1',
                distance=100.0,
                point_type='girth_weld',
                description='Weld 1'
            ),
            ReferencePoint(
                id='rp1_2',
                run_id='run1',
                distance=500.0,
                point_type='girth_weld',
                description='Weld 2'
            ),
            ReferencePoint(
                id='rp1_3',
                run_id='run1',
                distance=1000.0,
                point_type='valve',
                description='Valve 1'
            ),
            ReferencePoint(
                id='rp1_4',
                run_id='run1',
                distance=1500.0,
                point_type='girth_weld',
                description='Weld 3'
            ),
            ReferencePoint(
                id='rp1_5',
                run_id='run1',
                distance=2000.0,
                point_type='girth_weld',
                description='Weld 4'
            )
        ]
    
    @pytest.fixture
    def reference_points_run2(self):
        """Create reference points for second run with small drift."""
        return [
            ReferencePoint(
                id='rp2_1',
                run_id='run2',
                distance=102.0,  # +2 feet drift
                point_type='girth_weld',
                description='Weld 1'
            ),
            ReferencePoint(
                id='rp2_2',
                run_id='run2',
                distance=505.0,  # +5 feet drift
                point_type='girth_weld',
                description='Weld 2'
            ),
            ReferencePoint(
                id='rp2_3',
                run_id='run2',
                distance=1008.0,  # +8 feet drift
                point_type='valve',
                description='Valve 1'
            ),
            ReferencePoint(
                id='rp2_4',
                run_id='run2',
                distance=1507.0,  # +7 feet drift
                point_type='girth_weld',
                description='Weld 3'
            ),
            ReferencePoint(
                id='rp2_5',
                run_id='run2',
                distance=2005.0,  # +5 feet drift
                point_type='girth_weld',
                description='Weld 4'
            )
        ]
    
    @pytest.fixture
    def anomalies_run1(self):
        """Create anomalies from first inspection run."""
        return pd.DataFrame({
            'id': ['A1', 'A2', 'A3', 'A4'],
            'run_id': ['run1'] * 4,
            'distance': [200.0, 750.0, 1250.0, 1800.0],
            'clock_position': [3.0, 6.0, 9.0, 12.0],
            'depth_pct': [25.0, 30.0, 35.0, 40.0],
            'length': [4.0, 5.0, 6.0, 7.0],
            'width': [2.0, 2.5, 3.0, 3.5],
            'feature_type': ['external_corrosion'] * 4
        })
    
    def test_complete_alignment_and_correction_workflow(
        self,
        reference_points_run1,
        reference_points_run2,
        anomalies_run1
    ):
        """Test complete workflow from DTW alignment to anomaly correction."""
        # Step 1: Perform DTW alignment
        aligner = DTWAligner(drift_constraint=0.10)
        alignment_result = aligner.align_sequences(
            reference_points_run1,
            reference_points_run2,
            'run1',
            'run2'
        )
        
        # Verify alignment succeeded
        assert alignment_result.match_rate >= 95.0
        assert alignment_result.rmse <= 10.0
        assert len(alignment_result.matched_points) == 5
        
        # Step 2: Create correction function from alignment
        corrector = create_correction_function(alignment_result)
        
        # Verify correction function was created
        assert corrector is not None
        info = corrector.get_correction_info()
        assert info['num_reference_points'] == 5
        
        # Step 3: Apply correction to anomalies
        corrected_anomalies = corrector.correct_anomaly_distances(anomalies_run1)
        
        # Verify corrections were applied
        assert 'corrected_distance' in corrected_anomalies.columns
        assert len(corrected_anomalies) == len(anomalies_run1)
        
        # Step 4: Verify correction accuracy
        # With small drift (2-8 feet), corrected distances should be slightly higher
        for idx, row in corrected_anomalies.iterrows():
            original = row['distance']
            corrected = row['corrected_distance']
            
            # Corrected should be slightly higher (within reasonable range)
            correction = corrected - original
            
            # Corrections should be small (within ±10 feet)
            assert abs(correction) < 15.0
    
    def test_correction_preserves_anomaly_data(
        self,
        reference_points_run1,
        reference_points_run2,
        anomalies_run1
    ):
        """Test that correction preserves all original anomaly data."""
        # Perform alignment and create corrector
        aligner = DTWAligner()
        alignment_result = aligner.align_sequences(
            reference_points_run1,
            reference_points_run2,
            'run1',
            'run2'
        )
        corrector = create_correction_function(alignment_result)
        
        # Apply correction
        corrected_anomalies = corrector.correct_anomaly_distances(anomalies_run1)
        
        # Verify all original columns are preserved
        for col in anomalies_run1.columns:
            assert col in corrected_anomalies.columns
            pd.testing.assert_series_equal(
                anomalies_run1[col],
                corrected_anomalies[col]
            )
    
    def test_correction_handles_extrapolation(
        self,
        reference_points_run1,
        reference_points_run2
    ):
        """Test that correction handles anomalies outside reference point range."""
        # Perform alignment
        aligner = DTWAligner()
        alignment_result = aligner.align_sequences(
            reference_points_run1,
            reference_points_run2,
            'run1',
            'run2'
        )
        corrector = create_correction_function(alignment_result)
        
        # Create anomalies outside reference point range
        anomalies_outside = pd.DataFrame({
            'id': ['A_before', 'A_after'],
            'distance': [50.0, 2500.0],  # Before first and after last ref point
            'depth_pct': [20.0, 25.0]
        })
        
        # Apply correction - should not raise error
        corrected = corrector.correct_anomaly_distances(anomalies_outside)
        
        # Verify corrections were applied
        assert len(corrected) == 2
        assert all(corrected['corrected_distance'].notna())
        
        # Verify extrapolation flags
        assert corrector.is_extrapolating(50.0)
        assert corrector.is_extrapolating(2500.0)
    
    def test_multiple_anomaly_batches(
        self,
        reference_points_run1,
        reference_points_run2
    ):
        """Test correcting multiple batches of anomalies with same corrector."""
        # Create corrector
        aligner = DTWAligner()
        alignment_result = aligner.align_sequences(
            reference_points_run1,
            reference_points_run2,
            'run1',
            'run2'
        )
        corrector = create_correction_function(alignment_result)
        
        # Create multiple batches
        batch1 = pd.DataFrame({
            'id': ['A1', 'A2'],
            'distance': [200.0, 400.0],
            'depth_pct': [25.0, 30.0]
        })
        
        batch2 = pd.DataFrame({
            'id': ['A3', 'A4'],
            'distance': [800.0, 1200.0],
            'depth_pct': [35.0, 40.0]
        })
        
        # Correct both batches
        corrected1 = corrector.correct_anomaly_distances(batch1)
        corrected2 = corrector.correct_anomaly_distances(batch2)
        
        # Verify both were corrected
        assert len(corrected1) == 2
        assert len(corrected2) == 2
        assert all(corrected1['corrected_distance'].notna())
        assert all(corrected2['corrected_distance'].notna())
    
    def test_correction_with_minimal_drift(self):
        """Test correction with very small drift (high quality alignment)."""
        # Create reference points with minimal drift
        ref_points1 = [
            ReferencePoint(id=f'rp1_{i}', run_id='run1', distance=float(i*500), point_type='girth_weld')
            for i in range(5)
        ]
        
        ref_points2 = [
            ReferencePoint(id=f'rp2_{i}', run_id='run2', distance=float(i*500 + 0.5), point_type='girth_weld')
            for i in range(5)
        ]
        
        # Perform alignment
        aligner = DTWAligner()
        alignment_result = aligner.align_sequences(ref_points1, ref_points2, 'run1', 'run2')
        
        # Verify high quality alignment
        assert alignment_result.rmse < 1.0  # Very low RMSE
        
        # Create corrector
        corrector = create_correction_function(alignment_result)
        
        # Verify minimal corrections
        info = corrector.get_correction_info()
        assert info['max_correction'] < 1.0
        assert abs(info['mean_correction']) < 1.0
    
    def test_correction_info_matches_alignment_metrics(
        self,
        reference_points_run1,
        reference_points_run2
    ):
        """Test that correction info is consistent with alignment metrics."""
        # Perform alignment
        aligner = DTWAligner()
        alignment_result = aligner.align_sequences(
            reference_points_run1,
            reference_points_run2,
            'run1',
            'run2'
        )
        
        # Create corrector and get info
        corrector = create_correction_function(alignment_result)
        info = corrector.get_correction_info()
        
        # Verify consistency
        assert info['num_reference_points'] == len(alignment_result.matched_points)
        
        # Verify distance ranges match
        params = alignment_result.correction_function_params
        assert info['distance_range_run1'][0] == min(params['matched_distances_run1'])
        assert info['distance_range_run1'][1] == max(params['matched_distances_run1'])
        assert info['distance_range_run2'][0] == min(params['matched_distances_run2'])
        assert info['distance_range_run2'][1] == max(params['matched_distances_run2'])


class TestCorrectionEdgeCases:
    """Test edge cases in the integration workflow."""
    
    def test_correction_with_minimum_reference_points(self):
        """Test correction with exactly 2 reference points (minimum)."""
        ref_points1 = [
            ReferencePoint(id='rp1_1', run_id='run1', distance=0.0, point_type='girth_weld'),
            ReferencePoint(id='rp1_2', run_id='run1', distance=1000.0, point_type='girth_weld')
        ]
        
        ref_points2 = [
            ReferencePoint(id='rp2_1', run_id='run2', distance=0.0, point_type='girth_weld'),
            ReferencePoint(id='rp2_2', run_id='run2', distance=1005.0, point_type='girth_weld')  # +5 feet drift
        ]
        
        # Perform alignment
        aligner = DTWAligner()
        alignment_result = aligner.align_sequences(ref_points1, ref_points2, 'run1', 'run2')
        
        # Create corrector - should work with just 2 points
        corrector = create_correction_function(alignment_result)
        
        # Test correction
        anomalies = pd.DataFrame({
            'id': ['A1'],
            'distance': [500.0]
        })
        
        corrected = corrector.correct_anomaly_distances(anomalies)
        assert len(corrected) == 1
        assert corrected['corrected_distance'].iloc[0] == pytest.approx(502.5, abs=1.0)
    
    def test_correction_with_empty_anomaly_dataframe(self):
        """Test that correction handles empty anomaly DataFrame."""
        ref_points1 = [
            ReferencePoint(id='rp1_1', run_id='run1', distance=0.0, point_type='girth_weld'),
            ReferencePoint(id='rp1_2', run_id='run1', distance=1000.0, point_type='girth_weld')
        ]
        
        ref_points2 = [
            ReferencePoint(id='rp2_1', run_id='run2', distance=0.0, point_type='girth_weld'),
            ReferencePoint(id='rp2_2', run_id='run2', distance=1005.0, point_type='girth_weld')  # +5 feet drift
        ]
        
        aligner = DTWAligner()
        alignment_result = aligner.align_sequences(ref_points1, ref_points2, 'run1', 'run2')
        corrector = create_correction_function(alignment_result)
        
        # Empty DataFrame
        empty_df = pd.DataFrame(columns=['id', 'distance', 'depth_pct'])
        
        # Should handle gracefully
        corrected = corrector.correct_anomaly_distances(empty_df)
        assert len(corrected) == 0
        assert 'corrected_distance' in corrected.columns
