"""
Unit tests for HungarianMatcher class.
"""

import pytest
import numpy as np
from datetime import datetime
from src.matching.matcher import (
    HungarianMatcher,
    MatchConfidence,
    UnmatchedClassification
)
from src.matching.similarity import SimilarityCalculator
from src.data_models.models import AnomalyRecord


@pytest.fixture
def sample_anomalies_run1():
    """Create sample anomalies for first run."""
    return [
        AnomalyRecord(
            id="R1_A1",
            run_id="RUN1",
            distance=100.0,
            clock_position=3.0,
            feature_type="external_corrosion",
            depth_pct=45.0,
            length=12.0,
            width=6.0,
            inspection_date=datetime(2020, 1, 1)
        ),
        AnomalyRecord(
            id="R1_A2",
            run_id="RUN1",
            distance=200.0,
            clock_position=6.0,
            feature_type="external_corrosion",
            depth_pct=30.0,
            length=8.0,
            width=4.0,
            inspection_date=datetime(2020, 1, 1)
        ),
        AnomalyRecord(
            id="R1_A3",
            run_id="RUN1",
            distance=300.0,
            clock_position=9.0,
            feature_type="dent",
            depth_pct=20.0,
            length=10.0,
            width=5.0,
            inspection_date=datetime(2020, 1, 1)
        )
    ]


@pytest.fixture
def sample_anomalies_run2():
    """Create sample anomalies for second run (similar to run1 with growth)."""
    return [
        AnomalyRecord(
            id="R2_A1",
            run_id="RUN2",
            distance=101.0,  # Close to R1_A1
            clock_position=3.0,
            feature_type="external_corrosion",
            depth_pct=50.0,  # Grown from 45%
            length=13.0,
            width=6.5,
            inspection_date=datetime(2022, 1, 1)
        ),
        AnomalyRecord(
            id="R2_A2",
            run_id="RUN2",
            distance=199.0,  # Close to R1_A2
            clock_position=6.0,
            feature_type="external_corrosion",
            depth_pct=32.0,  # Grown from 30%
            length=8.5,
            width=4.2,
            inspection_date=datetime(2022, 1, 1)
        ),
        AnomalyRecord(
            id="R2_A3",
            run_id="RUN2",
            distance=500.0,  # New anomaly, far from others
            clock_position=12.0,
            feature_type="external_corrosion",
            depth_pct=25.0,
            length=7.0,
            width=3.0,
            inspection_date=datetime(2022, 1, 1)
        )
    ]


@pytest.fixture
def matcher():
    """Create HungarianMatcher instance."""
    return HungarianMatcher(confidence_threshold=0.6)


class TestHungarianMatcher:
    """Test suite for HungarianMatcher class."""
    
    def test_initialization(self):
        """Test matcher initialization with default and custom parameters."""
        # Default initialization
        matcher1 = HungarianMatcher()
        assert matcher1.confidence_threshold == 0.6
        assert matcher1.use_corrected_distance is True
        assert isinstance(matcher1.similarity_calculator, SimilarityCalculator)
        
        # Custom initialization
        custom_calc = SimilarityCalculator(distance_sigma=10.0)
        matcher2 = HungarianMatcher(
            similarity_calculator=custom_calc,
            confidence_threshold=0.7,
            use_corrected_distance=False
        )
        assert matcher2.confidence_threshold == 0.7
        assert matcher2.use_corrected_distance is False
        assert matcher2.similarity_calculator is custom_calc
    
    def test_create_cost_matrix(self, matcher, sample_anomalies_run1, sample_anomalies_run2):
        """Test cost matrix creation."""
        cost_matrix, similarity_matrix = matcher.create_cost_matrix(
            sample_anomalies_run1, sample_anomalies_run2
        )
        
        # Check shapes
        assert cost_matrix.shape == (3, 3)
        assert similarity_matrix.shape == (3, 3)
        
        # Check that cost = 1 - similarity
        np.testing.assert_array_almost_equal(
            cost_matrix, 1.0 - similarity_matrix
        )
        
        # Check that similarity values are in [0, 1]
        assert np.all(similarity_matrix >= 0.0)
        assert np.all(similarity_matrix <= 1.0)
        
        # Check that similar anomalies have high similarity
        # R1_A1 and R2_A1 should be most similar (both at ~100ft, 3 o'clock, external_corrosion)
        assert similarity_matrix[0, 0] > 0.8
    
    def test_solve_assignment(self, matcher, sample_anomalies_run1, sample_anomalies_run2):
        """Test Hungarian algorithm assignment."""
        cost_matrix, similarity_matrix = matcher.create_cost_matrix(
            sample_anomalies_run1, sample_anomalies_run2
        )
        
        assignments, confidences = matcher.solve_assignment(
            cost_matrix, similarity_matrix
        )
        
        # Check that we get assignments for all anomalies
        assert len(assignments) == 3
        assert len(confidences) == 3
        
        # Check that assignments are valid indices
        for i, j in assignments:
            assert 0 <= i < 3
            assert 0 <= j < 3
        
        # Check that each index appears at most once (one-to-one matching)
        run1_indices = [i for i, j in assignments]
        run2_indices = [j for i, j in assignments]
        assert len(set(run1_indices)) == len(run1_indices)
        assert len(set(run2_indices)) == len(run2_indices)
        
        # Check that confidences match similarity matrix
        for (i, j), conf in zip(assignments, confidences):
            assert conf == similarity_matrix[i, j]
    
    def test_filter_low_confidence(self, matcher):
        """Test filtering of low-confidence matches."""
        assignments = [(0, 0), (1, 1), (2, 2)]
        confidences = [0.9, 0.5, 0.7]  # One below threshold (0.6)
        
        filtered_assignments, filtered_confidences = matcher.filter_low_confidence(
            assignments, confidences
        )
        
        # Should filter out (1, 1) with confidence 0.5
        assert len(filtered_assignments) == 2
        assert len(filtered_confidences) == 2
        assert (0, 0) in filtered_assignments
        assert (2, 2) in filtered_assignments
        assert (1, 1) not in filtered_assignments
        assert 0.9 in filtered_confidences
        assert 0.7 in filtered_confidences
        assert 0.5 not in filtered_confidences
    
    def test_classify_confidence_level(self, matcher):
        """Test confidence level classification."""
        assert matcher.classify_confidence_level(0.9) == MatchConfidence.HIGH
        assert matcher.classify_confidence_level(0.8) == MatchConfidence.HIGH
        assert matcher.classify_confidence_level(0.75) == MatchConfidence.MEDIUM
        assert matcher.classify_confidence_level(0.6) == MatchConfidence.MEDIUM
        assert matcher.classify_confidence_level(0.5) == MatchConfidence.LOW
        assert matcher.classify_confidence_level(0.0) == MatchConfidence.LOW
    
    def test_classify_unmatched(self, matcher, sample_anomalies_run1, sample_anomalies_run2):
        """Test classification of unmatched anomalies."""
        # Simulate scenario where indices 0 and 1 are matched
        matched_indices_run1 = {0, 1}
        matched_indices_run2 = {0, 1}
        
        unmatched = matcher.classify_unmatched(
            sample_anomalies_run1,
            sample_anomalies_run2,
            matched_indices_run1,
            matched_indices_run2
        )
        
        # Check structure
        assert 'new' in unmatched
        assert 'repaired_or_removed' in unmatched
        
        # Check that unmatched anomalies are correctly identified
        assert len(unmatched['repaired_or_removed']) == 1
        assert unmatched['repaired_or_removed'][0].id == "R1_A3"
        
        assert len(unmatched['new']) == 1
        assert unmatched['new'][0].id == "R2_A3"
    
    def test_match_anomalies_complete_workflow(
        self, matcher, sample_anomalies_run1, sample_anomalies_run2
    ):
        """Test complete matching workflow."""
        result = matcher.match_anomalies(
            sample_anomalies_run1,
            sample_anomalies_run2,
            run1_id="RUN1",
            run2_id="RUN2"
        )
        
        # Check result structure
        assert 'matches' in result
        assert 'unmatched' in result
        assert 'statistics' in result
        
        # Check matches
        matches = result['matches']
        assert len(matches) >= 2  # At least R1_A1-R2_A1 and R1_A2-R2_A2
        
        # Check that matches have required fields
        for match in matches:
            assert hasattr(match, 'anomaly1_id')
            assert hasattr(match, 'anomaly2_id')
            assert hasattr(match, 'similarity_score')
            assert hasattr(match, 'confidence')
            assert match.similarity_score >= matcher.confidence_threshold
        
        # Check unmatched
        unmatched = result['unmatched']
        assert 'new' in unmatched
        assert 'repaired_or_removed' in unmatched
        
        # Check statistics
        stats = result['statistics']
        assert stats['total_run1'] == 3
        assert stats['total_run2'] == 3
        assert stats['matched'] == len(matches)
        assert stats['unmatched_run1'] + stats['matched'] == 3
        assert stats['unmatched_run2'] + stats['matched'] == 3
        assert 0.0 <= stats['match_rate'] <= 1.0
    
    def test_match_anomalies_empty_inputs(self, matcher):
        """Test matching with empty input lists."""
        # Both empty
        result1 = matcher.match_anomalies([], [], "RUN1", "RUN2")
        assert result1['matches'] == []
        assert result1['statistics']['matched'] == 0
        assert result1['statistics']['match_rate'] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
